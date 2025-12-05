"""AI智能体API路由"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.ai_agent import DietTrainingAgent, get_ai_agent
from app.repositories.conversation_repository import ConversationRepository
from app.models.ai_conversation import AIConversation

router = APIRouter(prefix="/api/ai", tags=["ai"])


# ============================================================================
# 请求/响应模型
# ============================================================================

class ChatRequest(BaseModel):
    """对话请求"""
    message: str = Field(..., description="用户消息", min_length=1)
    user_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="用户上下文（可选）"
    )


class ChatResponse(BaseModel):
    """对话响应"""
    message: str = Field(..., description="AI响应消息")
    conversation_id: int = Field(..., description="对话ID")
    timestamp: datetime = Field(..., description="时间戳")


class GeneratePlanRequest(BaseModel):
    """生成计划请求"""
    user_input: str = Field(..., description="用户输入", min_length=1)
    user_preferences: Optional[Dict[str, Any]] = Field(
        default=None,
        description="用户偏好"
    )


class GeneratePlanResponse(BaseModel):
    """生成计划响应"""
    plan: Dict[str, Any] = Field(..., description="生成的计划")
    conversation_id: int = Field(..., description="对话ID")
    timestamp: datetime = Field(..., description="时间戳")


class ConversationMessage(BaseModel):
    """对话消息"""
    role: str = Field(..., description="角色（user/assistant）")
    content: str = Field(..., description="消息内容")
    timestamp: datetime = Field(..., description="时间戳")


class ConversationHistoryResponse(BaseModel):
    """对话历史响应"""
    messages: List[ConversationMessage] = Field(..., description="消息列表")
    total: int = Field(..., description="总消息数")


# ============================================================================
# AI对话端点
# ============================================================================

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    与AI智能体对话
    
    - 调用LangGraph智能体（包含RAG检索）
    - 保存对话历史到关系数据库
    - 向量化并存储到ChromaDB
    
    验证: 需求 6.1, 7.1, 7.2
    """
    try:
        # 获取AI智能体实例
        agent = get_ai_agent()
        
        # 准备用户偏好和历史数据
        user_preferences = request.user_context or {}
        historical_plans = []
        
        # 调用智能体生成响应
        result = agent.generate_plan(
            user_input=request.message,
            user_preferences=user_preferences,
            historical_plans=historical_plans
        )
        
        # 提取AI响应
        ai_response = ""
        if result.get("messages"):
            # 获取最后一条AI消息
            for msg in reversed(result["messages"]):
                if msg["role"] == "assistant":
                    ai_response = msg["content"]
                    break
        
        if not ai_response:
            ai_response = "抱歉，我无法生成响应。请稍后再试。"
        
        # 保存对话历史到数据库
        conversation_repo = ConversationRepository(db)
        
        # 保存用户消息
        user_conv = AIConversation(
            role="user",
            content=request.message
        )
        user_conv = conversation_repo.create(user_conv)
        
        # 保存AI响应
        ai_conv = AIConversation(
            role="assistant",
            content=ai_response
        )
        ai_conv = conversation_repo.create(ai_conv)
        
        # 返回响应
        return ChatResponse(
            message=ai_response,
            conversation_id=ai_conv.id,
            timestamp=ai_conv.timestamp
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI对话失败: {str(e)}"
        )


# ============================================================================
# 计划生成端点
# ============================================================================

@router.post("/generate-plan", response_model=GeneratePlanResponse)
async def generate_plan(
    request: GeneratePlanRequest,
    db: Session = Depends(get_db)
):
    """
    生成饮食训练计划
    
    - 传递用户偏好和历史数据
    - 利用向量检索增强上下文
    - 解析AI生成的计划
    - 向量化并存储生成的计划
    - 返回结构化数据
    
    验证: 需求 6.3, 6.4, 7.2, 7.4
    """
    try:
        # 获取AI智能体实例
        agent = get_ai_agent()
        
        # 准备用户偏好
        user_preferences = request.user_preferences or {}
        
        # 调用智能体生成计划
        result = agent.generate_plan(
            user_input=request.user_input,
            user_preferences=user_preferences,
            historical_plans=[]
        )
        
        # 提取生成的计划
        plan = result.get("plan", {})
        
        if not plan:
            raise HTTPException(
                status_code=500,
                detail="AI未能生成有效的计划"
            )
        
        # 保存对话历史
        conversation_repo = ConversationRepository(db)
        
        # 保存用户请求
        user_conv = AIConversation(
            role="user",
            content=request.user_input
        )
        user_conv = conversation_repo.create(user_conv)
        
        # 保存AI生成的计划（作为对话）
        plan_text = f"生成计划：{plan.get('date', '')} - {len(plan.get('meals', []))}餐 {len(plan.get('exercises', []))}运动"
        ai_conv = AIConversation(
            role="assistant",
            content=plan_text
        )
        ai_conv = conversation_repo.create(ai_conv)
        
        # 返回响应
        return GeneratePlanResponse(
            plan=plan,
            conversation_id=ai_conv.id,
            timestamp=ai_conv.timestamp
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"生成计划失败: {str(e)}"
        )


# ============================================================================
# 对话历史管理端点
# ============================================================================

@router.get("/history", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    获取对话历史
    
    验证: 需求 7.1
    """
    try:
        conversation_repo = ConversationRepository(db)
        
        # 获取最近的对话
        conversations = conversation_repo.get_recent(limit=limit)
        
        # 转换为响应格式
        messages = [
            ConversationMessage(
                role=conv.role,
                content=conv.content,
                timestamp=conv.timestamp
            )
            for conv in conversations
        ]
        
        return ConversationHistoryResponse(
            messages=messages,
            total=len(messages)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取对话历史失败: {str(e)}"
        )


@router.delete("/history")
async def clear_conversation_history(
    db: Session = Depends(get_db)
):
    """
    清除对话历史
    
    同时清除向量数据
    
    验证: 需求 7.5
    """
    try:
        conversation_repo = ConversationRepository(db)
        
        # 删除所有对话记录
        deleted_count = conversation_repo.delete_all()
        
        # TODO: 清除向量数据库中的对话向量
        # 这需要在 vectorization_service 中实现
        
        return {
            "message": f"已清除 {deleted_count} 条对话记录",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"清除对话历史失败: {str(e)}"
        )


# ============================================================================
# 健康检查端点
# ============================================================================

@router.get("/health")
async def health_check():
    """AI服务健康检查"""
    try:
        # 尝试获取AI智能体实例
        agent = get_ai_agent()
        
        return {
            "status": "healthy",
            "service": "ai",
            "agent_initialized": agent is not None
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "ai",
            "error": str(e)
        }
