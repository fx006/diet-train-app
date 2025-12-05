"""
向量数据库服务 - ChromaDB

提供向量存储和检索功能，用于：
- 对话历史向量化和语义搜索
- 计划数据向量化和相似计划推荐
- 知识库向量化和RAG检索
"""
import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions


class VectorDBService:
    """向量数据库服务类"""
    
    def __init__(self, persist_directory: str = "./data/chroma"):
        """
        初始化向量数据库服务
        
        Args:
            persist_directory: ChromaDB 持久化存储目录
        """
        self.persist_directory = persist_directory
        
        # 确保目录存在
        os.makedirs(persist_directory, exist_ok=True)
        
        # 初始化 ChromaDB 客户端
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # 初始化 embedding 函数（支持自定义API base和模型）
        openai_api_key = os.getenv("OPENAI_API_KEY")
        openai_api_base = os.getenv("OPENAI_API_BASE")
        openai_embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        
        if openai_api_key:
            embedding_kwargs = {
                "api_key": openai_api_key,
                "model_name": openai_embedding_model  # 使用配置的模型
            }
            # 如果设置了自定义API base，添加到配置
            if openai_api_base:
                embedding_kwargs["api_base"] = openai_api_base
            
            self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(**embedding_kwargs)
        else:
            # 如果没有 OpenAI API key，使用默认的 embedding 函数
            self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        
        # 初始化集合
        self._init_collections()
    
    def _init_collections(self):
        """初始化向量集合"""
        # 对话历史集合
        self.conversations_collection = self.client.get_or_create_collection(
            name="conversations",
            embedding_function=self.embedding_function,
            metadata={
                "description": "User conversation history for semantic search",
                "hnsw:space": "cosine"
            }
        )
        
        # 计划数据集合
        self.plans_collection = self.client.get_or_create_collection(
            name="plans",
            embedding_function=self.embedding_function,
            metadata={
                "description": "Historical diet and exercise plans for similarity search",
                "hnsw:space": "cosine"
            }
        )
        
        # 知识库集合
        self.knowledge_collection = self.client.get_or_create_collection(
            name="knowledge",
            embedding_function=self.embedding_function,
            metadata={
                "description": "Nutrition and exercise knowledge base for RAG",
                "hnsw:space": "cosine"
            }
        )
    
    # ========================================================================
    # 对话历史操作
    # ========================================================================
    
    def add_conversation(
        self,
        conversation_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        添加对话到向量数据库
        
        Args:
            conversation_id: 对话唯一标识
            content: 对话内容
            metadata: 元数据（如时间戳、用户ID等）
        """
        # ChromaDB 要求 metadata 不能为空字典，如果为空则传 None
        meta = metadata if metadata else None
        
        self.conversations_collection.add(
            documents=[content],
            metadatas=[meta] if meta else None,
            ids=[conversation_id]
        )
    
    def search_similar_conversations(
        self,
        query: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索相似的对话
        
        Args:
            query: 查询文本
            n_results: 返回结果数量
            where: 过滤条件
            
        Returns:
            相似对话列表
        """
        results = self.conversations_collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where
        )
        
        return self._format_results(results)
    
    def delete_conversation(self, conversation_id: str):
        """删除对话"""
        try:
            self.conversations_collection.delete(ids=[conversation_id])
        except Exception:
            pass  # 如果不存在，忽略错误
    
    def clear_conversations(self):
        """清空所有对话"""
        self.client.delete_collection("conversations")
        self._init_collections()
    
    # ========================================================================
    # 计划数据操作
    # ========================================================================
    
    def add_plan(
        self,
        plan_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        添加计划到向量数据库
        
        Args:
            plan_id: 计划唯一标识
            content: 计划内容描述
            metadata: 元数据（如日期、类型、热量等）
        """
        # ChromaDB 要求 metadata 不能为空字典，如果为空则传 None
        meta = metadata if metadata else None
        
        self.plans_collection.add(
            documents=[content],
            metadatas=[meta] if meta else None,
            ids=[plan_id]
        )
    
    def search_similar_plans(
        self,
        query: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索相似的计划
        
        Args:
            query: 查询文本
            n_results: 返回结果数量
            where: 过滤条件
            
        Returns:
            相似计划列表
        """
        results = self.plans_collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where
        )
        
        return self._format_results(results)
    
    def delete_plan(self, plan_id: str):
        """删除计划"""
        try:
            self.plans_collection.delete(ids=[plan_id])
        except Exception:
            pass
    
    # ========================================================================
    # 知识库操作
    # ========================================================================
    
    def add_knowledge(
        self,
        knowledge_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        添加知识到向量数据库
        
        Args:
            knowledge_id: 知识唯一标识
            content: 知识内容
            metadata: 元数据（如类别、标签等）
        """
        # ChromaDB 要求 metadata 不能为空字典，如果为空则传 None
        meta = metadata if metadata else None
        
        self.knowledge_collection.add(
            documents=[content],
            metadatas=[meta] if meta else None,
            ids=[knowledge_id]
        )
    
    def add_knowledge_batch(
        self,
        knowledge_items: List[Dict[str, Any]]
    ):
        """
        批量添加知识
        
        Args:
            knowledge_items: 知识项列表，每项包含 id, content, metadata
        """
        ids = [item['id'] for item in knowledge_items]
        documents = [item['content'] for item in knowledge_items]
        metadatas = [item.get('metadata', {}) for item in knowledge_items]
        
        self.knowledge_collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
    
    def search_knowledge(
        self,
        query: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索知识库
        
        Args:
            query: 查询文本
            n_results: 返回结果数量
            where: 过滤条件
            
        Returns:
            相关知识列表
        """
        results = self.knowledge_collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where
        )
        
        return self._format_results(results)
    
    # ========================================================================
    # 辅助方法
    # ========================================================================
    
    def _format_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        格式化查询结果
        
        Args:
            results: ChromaDB 查询结果
            
        Returns:
            格式化后的结果列表
        """
        formatted = []
        
        if not results['ids'] or not results['ids'][0]:
            return formatted
        
        for i in range(len(results['ids'][0])):
            item = {
                'id': results['ids'][0][i],
                'document': results['documents'][0][i],
                'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                'distance': results['distances'][0][i] if results.get('distances') else None
            }
            formatted.append(item)
        
        return formatted
    
    def get_collection_stats(self) -> Dict[str, int]:
        """
        获取各集合的统计信息
        
        Returns:
            各集合的文档数量
        """
        return {
            'conversations': self.conversations_collection.count(),
            'plans': self.plans_collection.count(),
            'knowledge': self.knowledge_collection.count()
        }
    
    def reset_all(self):
        """重置所有集合（谨慎使用）"""
        self.client.reset()
        self._init_collections()


# 全局向量数据库服务实例
_vector_db_service: Optional[VectorDBService] = None


def get_vector_db() -> VectorDBService:
    """
    获取向量数据库服务实例（单例模式）
    
    Returns:
        VectorDBService 实例
    """
    global _vector_db_service
    
    if _vector_db_service is None:
        persist_dir = os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/chroma")
        _vector_db_service = VectorDBService(persist_directory=persist_dir)
    
    return _vector_db_service
