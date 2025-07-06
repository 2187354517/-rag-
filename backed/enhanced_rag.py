import os
import random
import signal
import time
import re
import asyncio
import logging
from constants import LLM_MODEL_NAME, MAX_SEQ_LENGTH, MAX_NEW_TOKENS, DEFAULT_TEMPERATURE, TOP_P, HISTORY_LIMIT, SEQGPT_MODEL_NAME
from knowledge_processor import EnhancedKnowledgeProcessor
from hybrid_retriever import HybridRetriever
import torch
import json
from typing import AsyncGenerator
from transformers import TextIteratorStreamer, AutoModelForCausalLM, AutoTokenizer
import threading
from queue import Empty
from llama_cpp import Llama  # 新增导入

HISTORY_LIMIT=6
os.environ["GGML_CUDA_MAX_DEVICE_BUF"] = "2048"  # 提升显存利用率
os.environ["OMP_NUM_THREADS"] = "10"        # OpenMP线程数
os.environ["GGML_OPENBLAS"] = "1"           # 启用OpenBLAS加速
os.environ["GGML_CUBLAS"] = "1"          # 启用CUDA BLAS加速

class EnhancedRAG:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        start_time = time.time()
        self.processor = EnhancedKnowledgeProcessor()
        self.chunks = self.processor.process_documents()
        self.retriever = HybridRetriever(self.chunks)
        
        self.llm = Llama(
            model_path=LLM_MODEL_NAME,
            n_gpu_layers=33,     # 启用全部GPU加速
            n_ctx=4096,          # 与模型训练长度一致
            n_batch=512,         # 根据显存调整
            n_threads=10,  # 在此处设置线程数
            seed=3029422349,
            # verbose=True
        )
        
        self.logger.info(f"模型加载完成，耗时：{time.time() - start_time:.2f}s")
        self.cache = {}

        # 初始化分类模型（使用SeqGPT）
        self.classification_tokenizer = AutoTokenizer.from_pretrained(SEQGPT_MODEL_NAME)
        self.classification_model = AutoModelForCausalLM.from_pretrained(SEQGPT_MODEL_NAME)
        if torch.cuda.is_available():
            self.classification_model = self.classification_model.half().cuda()
        self.classification_model.eval()
        self.GEN_TOK = '[GEN]'

    def _classify_question(self, question: str) -> bool:
        """使用SeqGPT模型进行问题分类"""
        # 构建分类提示
        labels = "数学问题，其他问题"
        prompt = f"输入: {question}\n分类: {labels}\n输出: {self.GEN_TOK}"
        
        # 编码输入
        inputs = self.classification_tokenizer(
            prompt, 
            return_tensors="pt", 
            padding=True, 
            truncation=True, 
            max_length=512
        )
        if torch.cuda.is_available():
            inputs = inputs.to('cuda')
        
        # 生成分类结果
        outputs = self.classification_model.generate(
            **inputs,
            num_beams=3,
            do_sample=False,
            max_new_tokens=10,
            early_stopping=True
        )
        
        # 解析响应
        response = self.classification_tokenizer.decode(
            outputs[0], 
            skip_special_tokens=True
        )
        
        # 提取生成内容
        if self.GEN_TOK in response:
            result = response.split(self.GEN_TOK)[1].strip()
        else:
            result = response.strip()
        
        # 调整匹配规则，只要分类结果中包含“输出: 数学问题”就判定为数学问题
        is_math = "输出: 数学问题" in response
        self.logger.info(f"分类结果: {result} => 数学问题? {is_math}")
        return is_math

    def _is_math_question(self, question: str) -> bool:
        """综合判断数学问题"""
        # 预处理问题
        processed_question = question.strip()
        if not processed_question.endswith('?'):
            processed_question += '?'
        
        # 使用SeqGPT模型分类
        is_math = self._classify_question(processed_question)
        
        # 保底关键词检查（仅当模型不确定时）
        if not is_math:
            math_keywords = {
                "方程", "函数", "导数", "积分", "矩阵", "概率", 
                "几何", "代数", "解", "证明", "公式", "计算"
            }
            keyword_count = sum(1 for kw in math_keywords if kw in question)
            is_math = keyword_count >= 2
        
        self.logger.info(f"最终数学问题判定: {is_math}")
        return is_math


    def _build_dialog_context(self, history):
        """优化的对话上下文构建（修复历史记录更新问题）"""
        self.logger.info("构建精简对话上下文")
        
        MAX_CHARS = 1000  # 字符数限制
        dialog_entries = []
        current_length = 0
        
        # 按时间倒序处理（从最新到最旧）
        for msg in reversed(history):
            content = msg["content"][:50]  # 截断单条消息长度
            role = "用户" if msg["role"] == "user" else "助手"
            entry = f"{role}：{content}"
            entry_length = len(entry)  # 包含角色和内容的完整长度
            
            if current_length + entry_length > MAX_CHARS:
                break
            
            dialog_entries.append(entry)  # 临时存储为倒序（最新在前）
            current_length += entry_length
        
        # 反转回正常时间顺序（最旧到最新）
        dialog_entries.reverse()
        
        # 保留最近N条（根据类常量配置）
        return dialog_entries[-6:] if 6 else dialog_entries
        
    def _build_chat_template(self, question, contexts, history):
        """优化的模板构建（修复历史记录截断问题）"""
        self.logger.info(f"构建高效对话模板")
        is_math = self._is_math_question(question)
        
        # 动态上下文处理
        MAX_CONTEXT_CHARS = 1500
        context_str = "\n".join([doc.page_content[:500] for doc in contexts[:3]]) if contexts else "无相关参考"
        context_str = context_str[:MAX_CONTEXT_CHARS]
        
        # 历史对话（保留最近的合理数量）
        dialog_history = self._build_dialog_context(history)  # 不再需要额外切片
        
        # 智能提示词构建
        system_prompt = """<|system|>
【会话记忆】
{history}

【参考知识】
{context}

【指令】
{instruction}
</s>"""

        instruction = (
            "作为数学专家，请用Markdown分步推导：1)问题分析 2)公式应用 3)计算过程 4)验证"
            if is_math else 
            "作为擅长交流的沟通者，请用自然语言回答，涉及公式时用LaTeX，保持口语化"
        )

        user_template = """<|user|>
{question}
</s>
<|assistant|>
"""

        return {
            "prompt": system_prompt.format(
                history="\n".join(dialog_history) or "无近期对话",
                context=context_str,
                instruction=instruction
            ) + user_template.format(question=question),
            "is_math": is_math
        }

    @property
    def last_prompt(self):
        """用于获取最后生成的prompt"""
        return self._last_prompt  # 在ask方法中保存生成的prompt

    async def ask(self, question: str, history: list = []) -> str:
        """同步生成完整回答"""
        try:
            self.logger.info(f"开始处理问题: {question[:50]}...")
            
            # 检索上下文
            contexts = await self.retriever.retrieve(question)
            self.logger.info(f"检索到{len(contexts)}条相关上下文")
            
            # 构建prompt
            template = self._build_chat_template(question, contexts, history)
            prompt = template["prompt"]
            self._last_prompt = prompt

            # 新增：打印提示词模板到控制台
            print("\n=== 生成的提示词模板 ===\n")
            print(prompt)
            print("\n=== 结束 ===\n")

            # GGUF生成配置
            generation_config = {
                "prompt": prompt,
                "max_tokens": MAX_NEW_TOKENS,
                "temperature": 0.3 if template["is_math"] else DEFAULT_TEMPERATURE,
                "top_p": TOP_P,
                "stop": ["</s>", "[INST]"],  # 停止标记
                "echo": False,               # 不返回prompt
                "mirostat_mode": 2,          # 智能采样
                "repeat_penalty": 1.2
            }
            
            # 生成回答
            response = self.llm.create_completion(**generation_config)
            full_text = response["choices"][0]["text"]
            
            return self._postprocess_response(full_text, prompt)
            
        except Exception as e:
            self.logger.error(f"处理异常：{str(e)}", exc_info=True)
            return "系统处理问题时遇到错误，请稍后再试。"

    def _postprocess_response(self, response, prompt):
        """后处理优化响应结果"""
        self.logger.info("开始后处理响应")
        response = response[len(prompt):].strip()

        # 清理对话历史残留
        response = re.sub(r'【对话上下文】.*?【当前问题】', '', response, flags=re.DOTALL)
        # 添加移除<｜end▁of▁of▁sentence▁>的逻辑
        response = re.sub(r"<\|end▁of▁of▁sentence▁\|>", '', response)
        self.logger.info(f"后处理后的响应: {response}")
        return response.strip()


    async def ask_stream(self, question: str, history: list = []) -> AsyncGenerator[str, None]:
        """流式生成回答"""
        try:
            self.logger.info(f"开始流式处理问题: {question[:50]}...")
            
            # 检索上下文
            contexts = await self.retriever.retrieve(question)
            
            # 构建prompt
            template = self._build_chat_template(question, contexts, history)
            prompt = template["prompt"]
            self._last_prompt = prompt

            # 新增：打印提示词模板到控制台
            print("\n=== 生成的提示词模板 ===\n")
            print(prompt)
            print("\n=== 结束 ===\n")            
            # 流式配置

            stream_config = {
                "prompt": prompt,
                "max_tokens": MAX_NEW_TOKENS,
                "temperature": 0.3 if template["is_math"] else DEFAULT_TEMPERATURE,
                "top_p": TOP_P,
                "stop": ["</s>", "[INST]"],
                "stream": True,
            }
            
            # 创建流式生成器
            stream = self.llm.create_completion(**stream_config)
            
            buffer = []
            async for chunk in self._async_stream_wrapper(stream):
                delta = chunk["choices"][0]["text"]
                
                # 缓冲区管理
                buffer.append(delta)
                if len(buffer) >= 3 or random.random() < 0.2:  # 动态flush
                    yield "".join(buffer)
                    buffer.clear()
                    
            # 返回剩余内容
            if buffer:
                yield "".join(buffer)
                
        except Exception as e:
            self.logger.error(f"流式生成失败: {str(e)}")
            yield "⚠️ 服务响应异常，请稍后重试"

    async def _async_stream_wrapper(self, generator):
        """将同步生成器转换为异步"""
        while True:
            try:
                yield next(generator)
            except StopIteration:
                break
            await asyncio.sleep(0.001)  # 防止事件循环阻塞

    async def _async_streamer(self, streamer):
        """改进的异步流处理器"""
        while True:
            try:
                for text in streamer:
                    # 移除特殊token
                    clean_text = re.sub(r'<\|.*?\|>', '', text)
                    if clean_text:
                        yield clean_text
                break
            except Empty:
                await asyncio.sleep(0.01)

    def _sanitize_response(self, text: str) -> str:
        """彻底净化响应文本"""
        # self.logger.info(f"开始净化响应文本: {text}")
        # 移除所有模板标记
        template_markers = [
            r"<\|.*?\|>", r"\[.*?\]", r"【.*?】",
            "无近期对话记录", "相关背景知识", "核心指令",
            "回答要求", "当前问题", "请按照上述要求生成回答"
        ]
        for marker in template_markers:
            text = re.sub(marker, "", text)

        # 移除模型特殊标记
        text = re.sub(r"<\|end▁of▁of▁sentence▁\|>", '', text)

        # 移除多余空行和首尾空格
        text = re.sub(r"\n{3,}", "\n\n", text.strip())

        # 过滤调试信息并去除末尾标点
        text = re.sub(r"DEBUG:\s.*", "", text)
        text = re.sub(r'[。，！？、,\.\s]+$', '', text)  # 新增的末尾标点清理
        # self.logger.info(f"净化后的响应文本: {text}")
        return text

    async def generate_related_questions(self, original_question: str, num_questions: int = 5) -> list:
        """生成相关问题（适配GGUF版本）"""
        try:
            self.logger.info(f"开始生成相关问题，原始问题: {original_question}")
            is_math = self._is_math_question(original_question)

            # 强化格式要求的提示词
            prompt = f"""<|system|>
请生成{num_questions}个独立的、无任何前缀且与原始问题高度相关的问题，严格遵守以下规则：
1. 每个问题独占一行，不要使用任何编号或符号开头
2. 问题长度不超过30个字
3. 不要使用Markdown格式

【原始问题】
{original_question}

</s>
<|user|>
请按要求生成{num_questions}个优质相关问题：
</s>
<|assistant|>
"""

            # 使用GGUF模型生成
            response = self.llm.create_completion(
                prompt=prompt,
                max_tokens=200,
                temperature=0.6,
                top_p=0.9,
                stop=["</s>", "[INST]"],
                echo=False  # 不返回原始prompt
            )

            # 提取生成内容
            full_response = response["choices"][0]["text"]
            generated_part = full_response[len(prompt):].strip() if full_response.startswith(prompt) else full_response
            
            self.logger.info(f"生成的相关问题响应: {generated_part}")
            return self._parse_questions(generated_part, is_math, num_questions)
            
        except Exception as e:
            self.logger.error(f"生成问题异常：{str(e)}")
            return []

    def _parse_questions(self, response, is_math=False, num_questions=3):
        """增强解析能力，支持多种列表格式"""
        self.logger.info(f"开始解析相关问题响应: {response}")
        num_questions = max(1, min(int(num_questions), 5))

        # 预处理：合并换行符和特殊空白
        response = re.sub(r'[\r\n]+', '\n', response).strip()

        # 模式匹配：增强的前缀识别模式
        pattern = r'''
            (?:^|\n)                     # 行首或换行符
            (?:                          # 匹配多种项目符号：
            \d+[\.、]?|                 # 数字编号 (如1. 或1、)
            [一二三四五六七八九十]+[\.、]| # 中文编号
            [•▶➢*\-]|                  # 项目符号
            问题\s*\d+\s*[:：]?|        # 问题1：格式
            题\s*\d+\s*[:：]?|         # 题1：格式
            [Qq]\s*\d+\s*[:：]|         # Q1: 格式
            )?
            \s*                         # 允许有空格
            (.*?)                       # 捕获问题内容
            (?=\n|$|(?<=\?))            # 前瞻断言结束位置
        '''
        matches = re.findall(pattern, response, re.VERBOSE | re.IGNORECASE)

        # 二次处理
        valid_questions = []
        for q in matches:
            # 强化清理前缀
            q = re.sub(
                r'^[\s\d•▶➢*\-\.、，：:问题Qq][\.、\s]*',  # 扩展前缀匹配范围
                '',
                q.strip(),
                flags=re.IGNORECASE
            )
            # 处理问号
            q = re.sub(r'\?+$', '?', q)  # 标准化问号
            if not is_math:
                q = re.sub(r'[。.]$', '?', q)
            # 长度和有效性检查
            if 6 <= len(q) <= 32 and (is_math or q.endswith('?')):
                valid_questions.append(q)

        # 保底处理：当正则匹配失败时按换行分割 + 二次清理
        if len(valid_questions) < num_questions:
            alt_questions = [
                re.sub(r'^[\s\d•▶➢*\-\.、，：:问题Qq][\.、\s]*', '', q.strip(), flags=re.I)
                for q in response.split('\n')
                if q.strip()
            ]
            valid_questions += [q for q in alt_questions if q][:num_questions * 2]

        # 最终处理流程
        seen = set()
        final_questions = []
        for q in valid_questions:
            # 最终清理残留符号
            q = re.sub(r'^[:：]\s*', '', q).strip()
            # 去重处理
            if q and q not in seen:
                seen.add(q)
                final_questions.append(q)

        self.logger.info(f"解析后的相关问题: {final_questions}")
        return final_questions[:num_questions]