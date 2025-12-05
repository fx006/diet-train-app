"""用户偏好API路由"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
import json

from app.database import get_db
from app.repositories.preference_repository import PreferenceRepository
from app.models.user_preference import UserPreference

router = APIRouter(prefix="/api/preferences", tags=["preferences"])


# ============================================================================
# 请求/响应模型
# ============================================================================

class UserPreferencesRequest(BaseModel):
    """用户偏好请求"""
    goal: Optional[str] = Field(None, description="目标（减脂/增肌/维持）")
    allergies: Optional[List[str]] = Field(None, description="过敏食物列表")
    dislikes: Optional[List[str]] = Field(None, description="不喜欢的食物列表")
    target_calories: Optional[int] = Field(None, description="目标热量", ge=0)
    activity_level: Optional[str] = Field(None, description="活动水平（低/中等/高）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "goal": "减脂",
                "allergies": ["花生", "海鲜"],
                "dislikes": ["香菜", "西兰花"],
                "target_calories": 1800,
                "activity_level": "中等"
            }
        }


class UserPreferencesResponse(BaseModel):
    """用户偏好响应"""
    goal: Optional[str] = None
    allergies: List[str] = []
    dislikes: List[str] = []
    target_calories: Optional[int] = None
    activity_level: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "goal": "减脂",
                "allergies": ["花生", "海鲜"],
                "dislikes": ["香菜"],
                "target_calories": 1800,
                "activity_level": "中等"
            }
        }


# ============================================================================
# 辅助函数
# ============================================================================

def serialize_list(items: List[str]) -> str:
    """将列表序列化为JSON字符串"""
    return json.dumps(items, ensure_ascii=False)


def deserialize_list(value: str) -> List[str]:
    """将JSON字符串反序列化为列表"""
    try:
        result = json.loads(value)
        return result if isinstance(result, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def get_preferences_dict(db: Session) -> Dict:
    """获取所有偏好并转换为字典"""
    repo = PreferenceRepository(db)
    all_prefs = repo.get_all()
    
    prefs_dict = {}
    for pref in all_prefs:
        if pref.key in ["allergies", "dislikes"]:
            prefs_dict[pref.key] = deserialize_list(pref.value)
        elif pref.key == "target_calories":
            try:
                prefs_dict[pref.key] = int(pref.value)
            except (ValueError, TypeError):
                prefs_dict[pref.key] = None
        else:
            prefs_dict[pref.key] = pref.value
    
    return prefs_dict


# ============================================================================
# API端点
# ============================================================================

@router.get("", response_model=UserPreferencesResponse)
async def get_preferences(db: Session = Depends(get_db)):
    """
    获取用户偏好
    
    返回用户的所有偏好设置，包括：
    - 目标（减脂/增肌/维持）
    - 过敏食物列表
    - 不喜欢的食物列表
    - 目标热量
    - 活动水平
    
    验证: 需求 7.3
    """
    try:
        prefs_dict = get_preferences_dict(db)
        
        return UserPreferencesResponse(
            goal=prefs_dict.get("goal"),
            allergies=prefs_dict.get("allergies", []),
            dislikes=prefs_dict.get("dislikes", []),
            target_calories=prefs_dict.get("target_calories"),
            activity_level=prefs_dict.get("activity_level")
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取用户偏好失败: {str(e)}"
        )


@router.put("", response_model=UserPreferencesResponse)
async def update_preferences(
    preferences: UserPreferencesRequest,
    db: Session = Depends(get_db)
):
    """
    更新用户偏好
    
    支持部分更新，只更新提供的字段。
    
    验证: 需求 7.3
    """
    try:
        repo = PreferenceRepository(db)
        
        # 更新各个偏好字段
        if preferences.goal is not None:
            repo.upsert("goal", preferences.goal)
        
        if preferences.allergies is not None:
            repo.upsert("allergies", serialize_list(preferences.allergies))
        
        if preferences.dislikes is not None:
            repo.upsert("dislikes", serialize_list(preferences.dislikes))
        
        if preferences.target_calories is not None:
            repo.upsert("target_calories", str(preferences.target_calories))
        
        if preferences.activity_level is not None:
            repo.upsert("activity_level", preferences.activity_level)
        
        # 返回更新后的偏好
        prefs_dict = get_preferences_dict(db)
        
        return UserPreferencesResponse(
            goal=prefs_dict.get("goal"),
            allergies=prefs_dict.get("allergies", []),
            dislikes=prefs_dict.get("dislikes", []),
            target_calories=prefs_dict.get("target_calories"),
            activity_level=prefs_dict.get("activity_level")
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"更新用户偏好失败: {str(e)}"
        )


@router.delete("")
async def delete_all_preferences(db: Session = Depends(get_db)):
    """
    删除所有用户偏好
    
    用于重置用户设置
    """
    try:
        repo = PreferenceRepository(db)
        deleted_count = repo.delete_all()
        
        return {
            "message": f"已删除 {deleted_count} 个偏好设置",
            "deleted_count": deleted_count
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"删除用户偏好失败: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """偏好服务健康检查"""
    return {
        "status": "healthy",
        "service": "preferences"
    }
