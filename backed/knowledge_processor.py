import re
import os
import logging
import hashlib
from langchain_experimental.text_splitter import SemanticChunker
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.document_loaders import DirectoryLoader, PyPDFLoader, TextLoader
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from json_loader import JSONLoader
from jsonl_loader import JSONLLoader
from constants import KNOWLEDGE_BASE_DIR, EMBED_MODEL_NAME, MIN_KNOWLEDGE_BASE_DOCS

class EnhancedKnowledgeProcessor:
    def __init__(self):
        self.embed_model = HuggingFaceEmbeddings(
            model_name=EMBED_MODEL_NAME,
            model_kwargs={"device": "cuda"},
            encode_kwargs={"batch_size": 8}
        )
        self._validate_knowledge_base()
        self.file_status_cache = {}  # 用于缓存文件状态

    def _validate_knowledge_base(self):
        """确保知识库满足最小数据量要求"""
        total_json_docs = 0
        
        # 遍历知识库目录中的所有文件
        for root, _, files in os.walk(KNOWLEDGE_BASE_DIR):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                
                # 只处理JSONL文件
                if file_name.lower().endswith(".jsonl"):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            # 统计文件中的JSON行数
                            lines = f.readlines()
                            total_json_docs += len(lines)
                    except Exception as e:
                        logging.error(f"处理文件 {file_path} 时出错: {e}")
        
        # 检查是否满足最小数据量要求
        if total_json_docs < MIN_KNOWLEDGE_BASE_DOCS:
            logging.warning(f"知识库当前数据量不足（{total_json_docs}条），建议补充更多数据")
        else:
            logging.info(f"知识库数据量验证通过，共 {total_json_docs} 条数据")


    def get_file_hash(self, file_path):
        """获取文件的哈希值，用于检测文件是否被修改"""
        if not os.path.exists(file_path):
            return None

        hasher = hashlib.md5()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()

    def process_documents(self):
        """处理知识库中的所有文档，动态更新知识库"""
        # 检查知识库目录是否存在
        if not os.path.exists(KNOWLEDGE_BASE_DIR):
            os.makedirs(KNOWLEDGE_BASE_DIR)
            return []

        # 获取知识库目录中的所有文件
        file_paths = []
        for root, _, files in os.walk(KNOWLEDGE_BASE_DIR):
            for file in files:
                file_paths.append(os.path.join(root, file))

        # 检查文件状态，只处理新增或修改的文件
        updated_files = []
        for file_path in file_paths:
            file_hash = self.get_file_hash(file_path)
            file_mtime = os.path.getmtime(file_path)

            # 如果文件不在缓存中，或者哈希值或修改时间发生变化，则需要重新处理
            if file_path not in self.file_status_cache:
                updated_files.append(file_path)
            else:
                cached_hash, cached_mtime = self.file_status_cache[file_path]
                if file_hash != cached_hash or file_mtime != cached_mtime:
                    updated_files.append(file_path)

        # 处理新增或修改的文件
        if updated_files:
            self._process_updated_files(updated_files)

        # 返回所有文档的分块
        return self._load_processed_chunks()

    def _process_updated_files(self, updated_files):
        """处理新增或修改的文件"""
        loaders = [
            DirectoryLoader(KNOWLEDGE_BASE_DIR, glob="**/*.pdf", loader_cls=PyPDFLoader),
            DirectoryLoader(KNOWLEDGE_BASE_DIR, glob="**/*.txt", loader_cls=TextLoader),
            DirectoryLoader(KNOWLEDGE_BASE_DIR, glob="**/*.json", loader_cls=JSONLoader),
            DirectoryLoader(KNOWLEDGE_BASE_DIR, glob="**/*.jsonl", loader_cls=JSONLLoader),
        ]

        # 加载所有文件
        all_documents = []
        for loader in loaders:
            all_documents.extend(loader.load())

        # 使用语义分块器处理文档
        chunker = SemanticChunker(
            embeddings=self.embed_model,
            breakpoint_threshold_amount=82,
            add_start_index=True
        )
        base_chunks = chunker.split_documents(all_documents)

        # 根据内容类型进一步分割
        final_chunks = []
        for chunk in base_chunks:
            content_type = self._detect_content_type(chunk.page_content)
            splitter = self._get_text_splitter(content_type)
            final_chunks.extend(splitter.split_documents([chunk]))

        # 更新分块缓存
        self._save_processed_chunks(final_chunks)

        # 更新文件状态缓存
        for file_path in updated_files:
            file_hash = self.get_file_hash(file_path)
            file_mtime = os.path.getmtime(file_path)
            self.file_status_cache[file_path] = (file_hash, file_mtime)

    def _load_processed_chunks(self):
        """加载已处理的分块"""
        # 如果没有缓存的分块，则重新处理所有文件
        if not hasattr(self, '_cached_chunks') or self._cached_chunks is None:
            self._cached_chunks = []
            self._process_updated_files([])  # 强制重新处理所有文件
        return self._cached_chunks

    def _save_processed_chunks(self, chunks):
        """保存处理后的分块"""
        self._cached_chunks = chunks

    def _detect_content_type(self, text):
        """检测内容类型（增加jsonl检测）"""
        if re.search(r'"instruction"\s*:|"input"\s*:|"output"\s*:', text) and \
           text.count('\n') >= 2 and \
           all(line.strip().startswith('{') for line in text.split('\n') if line.strip()):
            return "jsonl"
        if re.search(r'def |import |print\(|代码示例', text):
            return "code"
        elif re.search(r'\|.+\|', text) and '%' in text:
            return "table"
        elif re.search(r'"instruction":|"input":|"output":', text):
            return "json"
        return "normal"

    def _get_text_splitter(self, content_type):
        """根据内容类型获取文本分割器（优化jsonl处理）"""
        if content_type == "jsonl":
            return RecursiveCharacterTextSplitter(
                chunk_size=512,
                chunk_overlap=128,
                separators=["\n\n", "\n", "}", "{"]
            )
        if content_type == "code":
            return RecursiveCharacterTextSplitter(chunk_size=256, chunk_overlap=64)
        elif content_type == "table":
            return RecursiveCharacterTextSplitter(chunk_size=384, chunk_overlap=96)
        elif content_type == "json":
            return RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=128)
        return RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=128)