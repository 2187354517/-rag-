from io import BytesIO
import os
import torch
import requests  # 新增依赖
from PIL import Image
from transformers import AutoProcessor, BitsAndBytesConfig
from modelscope import Qwen2VLForConditionalGeneration
from constants import VL_OCR_MODEL_NAME
import torch
import requests
from PIL import Image
from transformers import AutoProcessor, BitsAndBytesConfig
from modelscope import Qwen2VLForConditionalGeneration

class MathOCRProcessor:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model, self.processor = self._load_model()

    def _load_model(self):
        """显存优化版模型加载方法"""
        try:
            # 更新量化配置
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,  # 改用float16节省显存
                llm_int8_enable_fp32_cpu_offload=True  # 启用CPU卸载
            )

            # 定制设备映射（关键修改）
            device_map = {
                "transformer.embed_tokens": 0,
                "transformer.layers": 0,
                "transformer.norm": 0,
                "lm_head": "cpu"  # 将头部模块放在CPU
            }

            processor = AutoProcessor.from_pretrained(
                VL_OCR_MODEL_NAME,
                use_fast=True,  # 启用快速处理器
                trust_remote_code=True
            )

            model = Qwen2VLForConditionalGeneration.from_pretrained(
                VL_OCR_MODEL_NAME,
                quantization_config=quantization_config,
                device_map=device_map,  # 自定义设备映射
                torch_dtype=torch.float16,
                offload_folder="./offload",  # 设置卸载目录
                trust_remote_code=True
            ).eval()

            return model, processor
        except Exception as e:
            raise RuntimeError(f"模型加载失败: {str(e)}")

    def _process_vision_info(self, messages):
        """增强版本地/网络图片处理器"""
        image_inputs = []
        for msg in messages:
            for content in msg["content"]:
                if content["type"] == "image":
                    img_source = content["image"]
                    
                    # 网络图片处理
                    if img_source.startswith(("http://", "https://")):
                        try:
                            response = requests.get(img_source, timeout=10)
                            response.raise_for_status()
                            image = Image.open(BytesIO(response.content))
                        except Exception as e:
                            raise ConnectionError(f"下载图片失败: {str(e)}")
                    
                    # 本地图片处理
                    else:
                        if not os.path.exists(img_source):
                            raise FileNotFoundError(f"图片路径不存在: {img_source}")
                        try:
                            image = Image.open(img_source).convert("RGB")
                        except Exception as e:
                            raise IOError(f"图片读取失败: {str(e)}")
                    
                    image_inputs.append(image)
        return image_inputs, []

    def process_image(self, image_path):
        """全流程数学公式识别"""
        try:
            # 构建对话消息
            messages = [{
                "role": "user",
                "content": [
                    {"type": "image", "image": image_path},
                    {"type": "text", "text": (
                        "请严格按以下要求识别数学内容：\n"
                        "1. 使用LaTeX格式输出所有公式\n"
                        "2. 保留文字与公式的相对位置\n"
                        "3. 复杂公式分步骤解析\n"
                        "示例：\n"
                        "文本：'根据公式可得' \n"
                        "公式：$E = mc^2$"
                    )}
                ]
            }]

            # 处理视觉输入
            image_inputs, _ = self._process_vision_info(messages)
            
            # 生成模型输入
            text = self.processor.apply_chat_template(
                messages, 
                tokenize=False, 
                add_generation_prompt=True
            )
            inputs = self.processor(
                text=[text],
                images=image_inputs,
                padding=True,
                return_tensors="pt"
            ).to(self.device)

            # 配置生成参数
            generate_kwargs = {
                "max_new_tokens": 1024,
                "temperature": 0.3,  # 降低随机性保证公式准确性
                "top_p": 0.85,
                "repetition_penalty": 1.2,
                "eos_token_id": self.processor.tokenizer.eos_token_id
            }

            # 执行推理
            with torch.no_grad():
                outputs = self.model.generate(**inputs, **generate_kwargs)
            
            # 解码并后处理
            result = self.processor.decode(
                outputs[0][len(inputs["input_ids"][0]):], 
                skip_special_tokens=True
            )
            return self._postprocess(result)

        except Exception as e:
            return f"处理失败: {str(e)}"

    def _postprocess(self, text):
        """专业级后处理"""
        # 清理特殊标记
        clean_text = text.replace("<|im_end|>", "").replace("<|im_start|>", "").strip()
        
        # LaTeX格式标准化
        clean_text = clean_text.replace("\\(", "$").replace("\\)", "$")  # 行内公式
        clean_text = clean_text.replace("\\[", "$$\n").replace("\\]", "\n$$")  # 块公式
        
        # 自动编号公式
        if "$" in clean_text:
            parts = clean_text.split("$")
            for i in range(1, len(parts), 2):
                parts[i] = f"公式({i//2+1}): ${parts[i]}$"
            clean_text = "".join(parts)
        
        return clean_text
    
# 在app = FastAPI()之后初始化OCR处理器
ocr_processor = MathOCRProcessor()

# 新增OCR处理接口
@app.post("/v1/ocr")
async def process_math_image(
    file: UploadFile = File(...),
    api_key: str = Security(get_api_key)
):
    """处理数学图片OCR"""
    try:
        # 验证API密钥
        user_id = auth.db.validate_api_key(api_key)
        if not user_id:
            raise HTTPException(401, "无效的API密钥")

        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # 处理图像
        result = ocr_processor.process_image(tmp_path)
        
        # 删除临时文件
        os.unlink(tmp_path)
        
        return {
            "status": "success",
            "ocr_result": result,
            "original_filename": file.filename
        }
    
    except Exception as e:
        logging.error(f"OCR处理失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"OCR处理失败: {str(e)}"}
        )