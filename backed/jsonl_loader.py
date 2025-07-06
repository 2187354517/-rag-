import json
import logging
from langchain.schema import Document

class JSONLLoader:
    """JSON Lines文件加载器"""

    def __init__(self, file_path):
        self.file_path = file_path

    def load(self):
        """加载并解析JSONL文件"""
        documents = []
        with open(self.file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    item = json.loads(line.strip())
                    content = self._format_content(item)
                    metadata = {
                        "source": self.file_path,
                        "line_number": line_num,
                        **{k: v for k, v in item.items() if k not in ['instruction', 'input', 'output']}
                    }
                    documents.append(Document(page_content=content, metadata=metadata))
                except json.JSONDecodeError as e:
                    logging.warning(f"解析JSONL文件失败：{self.file_path} 第{line_num}行，错误：{str(e)}")
        return documents

    def _format_content(self, item):
        """格式化单行内容"""
        parts = []
        if 'instruction' in item:
            parts.append(f"Instruction: {item['instruction']}")
        if 'input' in item:
            parts.append(f"Input: {item['input']}")
        if 'output' in item:
            parts.append(f"Output: {item['output']}")
        return "\n".join(parts)

    def lazy_load(self):
        """实现流式加载"""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    item = json.loads(line.strip())
                    content = self._format_content(item)
                    metadata = {
                        "source": self.file_path,
                        "line_number": line_num,
                        **{k: v for k, v in item.items() if k not in ['instruction', 'input', 'output']}
                    }
                    yield Document(page_content=content, metadata=metadata)
                except json.JSONDecodeError as e:
                    logging.warning(f"解析JSONL文件失败：{self.file_path} 第{line_num}行，错误：{str(e)}")

    