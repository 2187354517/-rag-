import json
from langchain.schema import Document

class JSONLoader:
    def __init__(self, file_path):
        self.file_path = file_path

    def load(self):
        """加载并解析 JSON 文件"""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        documents = []
        for item in data:
            content = f"Instruction: {item['instruction']}\nInput: {item['input']}\nOutput: {item['output']}"
            metadata = {
                "source": self.file_path,
                "instruction": item['instruction'],
                "input": item['input'],
                "output": item['output']
            }
            documents.append(Document(page_content=content, metadata=metadata))
        return documents

    def lazy_load(self):
        """实现 lazy_load 方法以支持 DirectoryLoader"""
        return iter(self.load())

    