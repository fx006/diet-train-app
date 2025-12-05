"""
向量化服务

提供高级的向量化和语义搜索功能，用于：
- 对话历史的向量化和检索
- 计划数据的向量化和相似推荐
- 知识库的向量化和RAG检索
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.services.vector_db import get_vector_db
from app.models.plan import Plan
from app.models.ai_conversation import AIConversation


class VectorizationService:
    """向量化服务类"""
    
    def __init__(self):
        """初始化向量化服务"""
        self.vector_db = get_vector_db()
    
    # ========================================================================
    # 对话向量化
    # ========================================================================
    
    def vectorize_conversation(
        self,
        conversation: AIConversation
    ) -> str:
        """
        向量化单个对话并存储
        
        Args:
            conversation: 对话对象
            
        Returns:
            向量ID
        """
        conversation_id = f"conv_{conversation.id}"
        
        # 构建对话内容
        content = f"{conversation.role}: {conversation.content}"
        
        # 构建元数据
        metadata = {
            "role": conversation.role,
            "timestamp": conversation.timestamp.isoformat() if conversation.timestamp else datetime.now().isoformat(),
            "conversation_id": str(conversation.id)
        }
        
        # 添加到向量数据库
        self.vector_db.add_conversation(
            conversation_id=conversation_id,
            content=content,
            metadata=metadata
        )
        
        return conversation_id
    
    def vectorize_conversations_batch(
        self,
        conversations: List[AIConversation]
    ) -> List[str]:
        """
        批量向量化对话
        
        Args:
            conversations: 对话列表
            
        Returns:
            向量ID列表
        """
        ids = []
        for conv in conversations:
            conv_id = self.vectorize_conversation(conv)
            ids.append(conv_id)
        return ids
    
    def search_relevant_conversations(
        self,
        query: str,
        n_results: int = 5,
        role_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索相关对话
        
        Args:
            query: 查询文本
            n_results: 返回结果数量
            role_filter: 角色过滤（user/assistant）
            
        Returns:
            相关对话列表
        """
        where = {"role": role_filter} if role_filter else None
        
        results = self.vector_db.search_similar_conversations(
            query=query,
            n_results=n_results,
            where=where
        )
        
        return results
    
    # ========================================================================
    # 计划向量化
    # ========================================================================
    
    def vectorize_plan(
        self,
        plan: Plan
    ) -> str:
        """
        向量化单个计划并存储
        
        Args:
            plan: 计划对象
            
        Returns:
            向量ID
        """
        plan_id = f"plan_{plan.id}"
        
        # 构建计划描述
        if plan.type == 'meal':
            content = f"餐食计划：{plan.name}，热量：{plan.calories}卡路里"
        else:
            content = f"运动计划：{plan.name}，时长：{plan.duration}分钟，消耗：{plan.calories}卡路里"
        
        # 构建元数据
        metadata = {
            "plan_id": str(plan.id),
            "date": plan.date.isoformat(),
            "type": plan.type,
            "name": plan.name,
            "calories": float(plan.calories)
        }
        
        if plan.duration:
            metadata["duration"] = plan.duration
        
        # 添加到向量数据库
        self.vector_db.add_plan(
            plan_id=plan_id,
            content=content,
            metadata=metadata
        )
        
        return plan_id
    
    def vectorize_plans_batch(
        self,
        plans: List[Plan]
    ) -> List[str]:
        """
        批量向量化计划
        
        Args:
            plans: 计划列表
            
        Returns:
            向量ID列表
        """
        ids = []
        for plan in plans:
            plan_id = self.vectorize_plan(plan)
            ids.append(plan_id)
        return ids
    
    def search_similar_plans(
        self,
        query: str,
        n_results: int = 5,
        plan_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索相似计划
        
        Args:
            query: 查询文本（如"低热量餐食"、"有氧运动"）
            n_results: 返回结果数量
            plan_type: 计划类型过滤（meal/exercise）
            
        Returns:
            相似计划列表
        """
        where = {"type": plan_type} if plan_type else None
        
        results = self.vector_db.search_similar_plans(
            query=query,
            n_results=n_results,
            where=where
        )
        
        return results
    
    def get_plan_recommendations(
        self,
        user_goal: str,
        plan_type: str,
        n_results: int = 3
    ) -> List[Dict[str, Any]]:
        """
        根据用户目标获取计划推荐
        
        Args:
            user_goal: 用户目标（如"减脂"、"增肌"）
            plan_type: 计划类型（meal/exercise）
            n_results: 返回结果数量
            
        Returns:
            推荐计划列表
        """
        # 构建查询
        if plan_type == 'meal':
            if '减' in user_goal or '脂' in user_goal:
                query = "低热量健康餐食"
            elif '增' in user_goal or '肌' in user_goal:
                query = "高蛋白增肌餐食"
            else:
                query = "营养均衡餐食"
        else:
            if '减' in user_goal or '脂' in user_goal:
                query = "有氧燃脂运动"
            elif '增' in user_goal or '肌' in user_goal:
                query = "力量训练增肌运动"
            else:
                query = "全面健身运动"
        
        return self.search_similar_plans(
            query=query,
            n_results=n_results,
            plan_type=plan_type
        )
    
    # ========================================================================
    # 知识库检索（RAG）
    # ========================================================================
    
    def search_knowledge_for_rag(
        self,
        query: str,
        n_results: int = 3,
        category: Optional[str] = None
    ) -> str:
        """
        搜索知识库用于RAG（检索增强生成）
        
        Args:
            query: 查询文本
            n_results: 返回结果数量
            category: 类别过滤（nutrition/exercise）
            
        Returns:
            格式化的知识文本，可直接用于LLM上下文
        """
        where = {"category": category} if category else None
        
        results = self.vector_db.search_knowledge(
            query=query,
            n_results=n_results,
            where=where
        )
        
        if not results:
            return "未找到相关知识。"
        
        # 格式化知识文本
        knowledge_text = "相关知识：\n\n"
        for i, result in enumerate(results, 1):
            knowledge_text += f"{i}. {result['document']}\n\n"
        
        return knowledge_text.strip()
    
    def get_nutrition_knowledge(
        self,
        topic: str,
        n_results: int = 3
    ) -> str:
        """
        获取营养相关知识
        
        Args:
            topic: 主题（如"蛋白质"、"碳水化合物"）
            n_results: 返回结果数量
            
        Returns:
            营养知识文本
        """
        return self.search_knowledge_for_rag(
            query=topic,
            n_results=n_results,
            category="nutrition"
        )
    
    def get_exercise_knowledge(
        self,
        topic: str,
        n_results: int = 3
    ) -> str:
        """
        获取运动相关知识
        
        Args:
            topic: 主题（如"有氧运动"、"力量训练"）
            n_results: 返回结果数量
            
        Returns:
            运动知识文本
        """
        return self.search_knowledge_for_rag(
            query=topic,
            n_results=n_results,
            category="exercise"
        )
    
    # ========================================================================
    # 上下文构建
    # ========================================================================
    
    def build_context_for_ai(
        self,
        user_query: str,
        include_conversations: bool = True,
        include_plans: bool = True,
        include_knowledge: bool = True
    ) -> Dict[str, Any]:
        """
        为AI构建完整的上下文
        
        Args:
            user_query: 用户查询
            include_conversations: 是否包含历史对话
            include_plans: 是否包含相似计划
            include_knowledge: 是否包含知识库
            
        Returns:
            包含各种上下文的字典
        """
        context = {
            "query": user_query,
            "conversations": [],
            "plans": [],
            "knowledge": ""
        }
        
        if include_conversations:
            context["conversations"] = self.search_relevant_conversations(
                query=user_query,
                n_results=3
            )
        
        if include_plans:
            context["plans"] = self.search_similar_plans(
                query=user_query,
                n_results=3
            )
        
        if include_knowledge:
            context["knowledge"] = self.search_knowledge_for_rag(
                query=user_query,
                n_results=3
            )
        
        return context
    
    # ========================================================================
    # 统计和管理
    # ========================================================================
    
    def get_stats(self) -> Dict[str, int]:
        """
        获取向量数据库统计信息
        
        Returns:
            统计信息字典
        """
        return self.vector_db.get_collection_stats()
    
    def clear_all_conversations(self):
        """清空所有对话向量"""
        self.vector_db.clear_conversations()
    
    def delete_plan_vector(self, plan_id: int):
        """删除计划向量"""
        vector_id = f"plan_{plan_id}"
        self.vector_db.delete_plan(vector_id)


# 全局向量化服务实例
_vectorization_service: Optional[VectorizationService] = None


def get_vectorization_service() -> VectorizationService:
    """
    获取向量化服务实例（单例模式）
    
    Returns:
        VectorizationService 实例
    """
    global _vectorization_service
    
    if _vectorization_service is None:
        _vectorization_service = VectorizationService()
    
    return _vectorization_service
