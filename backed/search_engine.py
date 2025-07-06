import logging
from fastapi import  Depends, Query
from fastapi.security import HTTPBearer
from typing import  List, Dict, Any
import time
import os
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from constants import MULTILINGUAL_MODEL_NAME

security_scheme = HTTPBearer()

# 添加搜索引擎类
class SearchEngine:
    def __init__(self, cache_dir=r"E:\math-ai\math-ai-backend\search_cache"):
        """初始化搜索引擎，仅从本地路径加载模型"""
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        # 仅从本地路径加载模型
        local_model_path = MULTILINGUAL_MODEL_NAME
        
        try:
            if os.path.exists(local_model_path):
                logging.info(f"使用本地多语言模型: {local_model_path}")
                self.model = SentenceTransformer(local_model_path)
                logging.info(f"成功加载搜索模型")
            else:
                logging.error(f"本地模型路径不存在: {local_model_path}")
                self.model = None
        except Exception as e:
            logging.error(f"加载搜索模型失败: {str(e)}")
            self.model = None
  
    def _keyword_search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """使用关键词匹配进行搜索"""
        if self.resources is None:
            return []
            
        query_words = set(query.lower().split())
        
        # 计算每个资源的关键词匹配度
        resource_scores = []
        for i, resource in enumerate(self.resources):
            # 构建资源文本
            resource_text = f"{resource.get('title', '').lower()} {resource.get('description', '').lower()} {' '.join(resource.get('tags', []))}"
            resource_words = set(resource_text.split())
            
            # 计算关键词重叠度
            overlap = len(query_words.intersection(resource_words))
            score = overlap / max(1, len(query_words))
            
            resource_scores.append((i, score))
        
        # 按分数排序
        resource_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 构建结果
        results = []
        for i, score in resource_scores[:max_results]:
            if score > 0:  # 只返回有匹配的结果
                resource = self.resources[i]
                results.append({
                    "file_name": resource.get("title", "未命名资源"),
                    "file_path": resource.get("url", "#"),
                    "file_type": resource.get("file_type", "html"),
                    "description": resource.get("description", ""),
                    "similarity": float(score)
                })
        
        return results
    
    def _cache_results(self, cache_file: str, results: List[Dict[str, Any]]):
        """缓存搜索结果"""
        try:
            cache_data = {
                "timestamp": time.time(),
                "results": results
            }
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"缓存搜索结果失败: {str(e)}")