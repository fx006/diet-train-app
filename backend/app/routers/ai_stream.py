"""
AI 流式输出 API

实现 Server-Sent Events (SSE) 支持流式生成
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import json
import asyncio

from app.services.diet_agent_v2 import create_diet_agent, UserContext


router = APIRouter(prefix="/api/ai", tags=["AI Streaming"])


# ============================================================================
# 请求/响应模型
# ============================================================================

class StreamPlanRequest(BaseModel):
    """流式生成计划请求"""
    user_request: str
    user_id: str
    age: int
    gender: str
    weight: float
    height: float
    goal: str
    activity_level: str
    allergies: Optional[List[str]] = []
    dislikes: Optional[List[str]] = []
    thread_id: Optional[str] = None


class ChatMessage(BaseModel):
    """聊天消息"""
    role: str
    content: str


class StreamChatRequest(BaseModel):
    """流式对话请求"""
    message: str
    user_id: str
    age: int
    gender: str
    weight: float
    height: float
    goal: str
    activity_level: str
    allergies: Optional[List[str]] = []
    dislikes: Optional[List[str]] = []
    thread_id: str


# ============================================================================
# 流式输出端点
# ============================================================================

@router.post("/stream/generate-plan")
async def stream_generate_plan(request: StreamPlanRequest):
    """
    流式生成饮食训练计划
    
    使用 Server-Sent Events (SSE) 实时返回生成过程
    
    Args:
        request: 包含用户信息和请求的数据
        
    Returns:
        StreamingResponse: SSE 流式响应
    """
    try:
        # 创建 agent
        agent = create_diet_agent()
        
        # 创建用户上下文
        user_ctx = UserContext(
            user_id=request.user_id,
            age=request.age,
            gender=request.gender,
            weight=request.weight,
            height=request.height,
            goal=request.goal,
            activity_level=request.activity_level,
            allergies=request.allergies or [],
            dislikes=request.dislikes or []
        )
        
        # 定义流式生成器
        async def event_generator():
            """SSE 事件生成器"""
            try:
                # 发送开始事件
                yield f"data: {json.dumps({'type': 'start', 'message': '开始生成计划...'})}\n\n"
                
                # 流式生成计划
                chunk_count = 0
                async for chunk in agent.stream_plan_generation(
                    request.user_request,
                    user_ctx,
                    request.thread_id
                ):
                    chunk_count += 1
                    
                    # 提取消息内容
                    if chunk.get("messages"):
                        latest_msg = chunk["messages"][-1]
                        
                        # 发送内容块
                        if hasattr(latest_msg, 'content') and latest_msg.content:
                            event_data = {
                                'type': 'content',
                                'chunk_id': chunk_count,
                                'content': latest_msg.content,
                                'role': getattr(latest_msg, 'role', 'assistant')
                            }
                            yield f"data: {json.dumps(event_data)}\n\n"
                    
                    # 检查是否有结构化响应
                    if chunk.get("structured_response"):
                        structured_data = {
                            'type': 'structured',
                            'data': chunk["structured_response"]
                        }
                        yield f"data: {json.dumps(structured_data)}\n\n"
                    
                    # 小延迟，避免过快
                    await asyncio.sleep(0.01)
                
                # 发送完成事件
                yield f"data: {json.dumps({'type': 'done', 'message': '计划生成完成', 'total_chunks': chunk_count})}\n\n"
                
            except Exception as e:
                # 发送错误事件
                error_data = {
                    'type': 'error',
                    'message': str(e)
                }
                yield f"data: {json.dumps(error_data)}\n\n"
        
        # 返回 SSE 响应
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # 禁用 nginx 缓冲
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream/chat")
async def stream_chat(request: StreamChatRequest):
    """
    流式对话
    
    继续之前的对话，使用 SSE 实时返回响应
    
    Args:
        request: 包含消息和用户信息的数据
        
    Returns:
        StreamingResponse: SSE 流式响应
    """
    try:
        # 创建 agent
        agent = create_diet_agent()
        
        # 创建用户上下文
        user_ctx = UserContext(
            user_id=request.user_id,
            age=request.age,
            gender=request.gender,
            weight=request.weight,
            height=request.height,
            goal=request.goal,
            activity_level=request.activity_level,
            allergies=request.allergies or [],
            dislikes=request.dislikes or []
        )
        
        # 定义流式生成器
        async def event_generator():
            """SSE 事件生成器"""
            try:
                # 发送开始事件
                yield f"data: {json.dumps({'type': 'start', 'message': '处理中...'})}\n\n"
                
                # 流式生成响应
                chunk_count = 0
                async for chunk in agent.stream_plan_generation(
                    request.message,
                    user_ctx,
                    request.thread_id
                ):
                    chunk_count += 1
                    
                    # 提取消息内容
                    if chunk.get("messages"):
                        latest_msg = chunk["messages"][-1]
                        
                        # 发送内容块
                        if hasattr(latest_msg, 'content') and latest_msg.content:
                            event_data = {
                                'type': 'content',
                                'chunk_id': chunk_count,
                                'content': latest_msg.content,
                                'role': getattr(latest_msg, 'role', 'assistant')
                            }
                            yield f"data: {json.dumps(event_data)}\n\n"
                    
                    # 检查是否有结构化响应
                    if chunk.get("structured_response"):
                        structured_data = {
                            'type': 'structured',
                            'data': chunk["structured_response"]
                        }
                        yield f"data: {json.dumps(structured_data)}\n\n"
                    
                    # 小延迟
                    await asyncio.sleep(0.01)
                
                # 发送完成事件
                yield f"data: {json.dumps({'type': 'done', 'message': '响应完成', 'total_chunks': chunk_count})}\n\n"
                
            except Exception as e:
                # 发送错误事件
                error_data = {
                    'type': 'error',
                    'message': str(e)
                }
                yield f"data: {json.dumps(error_data)}\n\n"
        
        # 返回 SSE 响应
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 健康检查
# ============================================================================

@router.get("/stream/health")
async def stream_health():
    """流式 API 健康检查"""
    return {
        "status": "healthy",
        "streaming": "enabled",
        "protocol": "Server-Sent Events (SSE)"
    }
