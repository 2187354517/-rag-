import asyncio
from langchain.vectorstores import Chroma
from langchain.retrievers import BM25Retriever, EnsembleRetriever
from sentence_transformers import CrossEncoder
from langchain.embeddings import HuggingFaceEmbeddings
from constants import VECTOR_DB_DIR, EMBED_MODEL_NAME, RERANKER_MODEL_NAME
import torch

class HybridRetriever:
    def __init__(self, chunks):

        # 加载嵌入模型
        self.embedding_model = HuggingFaceEmbeddings(
            model_name=EMBED_MODEL_NAME
        )

        # 初始化向量数据库
        self.vector_db = Chroma.from_documents(
            chunks,
            embedding=self.embedding_model,
            persist_directory=VECTOR_DB_DIR
        )

        # 初始化 BM25 检索器
        self.bm25_retriever = BM25Retriever.from_documents(chunks, k=5)

        # 初始化集成检索器
        self.ensemble_retriever = EnsembleRetriever(
            retrievers=[
                self.vector_db.as_retriever(search_kwargs={"k": 5}),
                self.bm25_retriever
            ],
            weights=[0.6, 0.4]
        )

        # 加载重排序模型
        self.reranker = CrossEncoder(
            model_name_or_path=RERANKER_MODEL_NAME,
            device="cuda" if torch.cuda.is_available() else "cpu"
        )

    async def retrieve(self, query, top_k=1):
        """检索相关文档"""
        try:
            loop = asyncio.get_running_loop()
            relevant_docs_task = loop.run_in_executor(None, self.ensemble_retriever.get_relevant_documents, query)
            relevant_docs = await relevant_docs_task
            if not relevant_docs:
                return []
            scores_task = loop.run_in_executor(None, self.reranker.predict, [[query, doc.page_content] for doc in relevant_docs])
            scores = await scores_task
            threshold = 0.85
            relevant_docs = [doc for doc, score in zip(relevant_docs, scores) if score > threshold]
            ranked_docs = sorted(zip(relevant_docs, scores), key=lambda x: x[1], reverse=True)
            return [doc for doc, _ in ranked_docs[:top_k]]
        except Exception as e:
            import logging
            logging.error(f"检索过程中发生错误: {str(e)}", exc_info=True)
            return []
        