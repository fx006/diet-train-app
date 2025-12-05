"""
增强的工具集合 - 使用 LangChain 1.x ToolRuntime 模式

这些工具展示了如何使用运行时上下文注入来访问：
- 用户个人信息
- 数据库数据
- 用户偏好
- 历史记录
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta

from langchain.tools import tool, ToolRuntime
from sqlalchemy.orm import Session

# 数据库相关导入（可选，如果需要访问数据库）
# from app.database import get_db
# from app.repositories.preference_repository import PreferenceRepository


# ============================================================================
# 1. 扩展的用户上下文
# ============================================================================

@dataclass
class EnhancedUserContext:
    """
    增强的用户上下文 - 包含更多信息
    
    这个上下文会自动注入到所有工具中，工具可以通过 runtime.context 访问
    """
    # 基本信息
    user_id: str
    age: int
    gender: str  # male/female
    weight: float  # kg
    height: float  # cm
    goal: str  # lose_weight, gain_muscle, maintain
    activity_level: str  # sedentary, light, moderate, active, very_active
    
    # 偏好信息
    allergies: List[str] = None
    dislikes: List[str] = None
    preferred_cuisines: List[str] = None  # 喜欢的菜系
    dietary_restrictions: List[str] = None  # 饮食限制（素食、低碳等）
    
    # 时间信息
    timezone: str = "Asia/Shanghai"
    preferred_meal_times: Dict[str, str] = None  # {"breakfast": "07:00", "lunch": "12:00", "dinner": "18:00"}
    
    # 运动偏好
    preferred_exercises: List[str] = None
    exercise_limitations: List[str] = None  # 运动限制
    available_equipment: List[str] = None  # 可用器材
    
    # 数据库会话（用于工具访问数据库）
    db_session: Optional[Session] = None
    
    def __post_init__(self):
        """初始化默认值"""
        if self.allergies is None:
            self.allergies = []
        if self.dislikes is None:
            self.dislikes = []
        if self.preferred_cuisines is None:
            self.preferred_cuisines = []
        if self.dietary_restrictions is None:
            self.dietary_restrictions = []
        if self.preferred_meal_times is None:
            self.preferred_meal_times = {
                "breakfast": "07:00",
                "lunch": "12:00",
                "dinner": "18:00"
            }
        if self.preferred_exercises is None:
            self.preferred_exercises = []
        if self.exercise_limitations is None:
            self.exercise_limitations = []
        if self.available_equipment is None:
            self.available_equipment = []


# ============================================================================
# 2. 基础计算工具
# ============================================================================

@tool
def calculate_bmr(runtime: ToolRuntime) -> float:
    """
    计算基础代谢率 (BMR)
    
    使用 ToolRuntime 自动获取用户的身体数据
    无需手动传递参数
    
    Returns:
        基础代谢率（卡路里/天）
    """
    ctx = runtime.context
    
    if ctx.gender.lower() == "male":
        bmr = 10 * ctx.weight + 6.25 * ctx.height - 5 * ctx.age + 5
    else:
        bmr = 10 * ctx.weight + 6.25 * ctx.height - 5 * ctx.age - 161
    
    return round(bmr, 2)


@tool
def calculate_tdee(runtime: ToolRuntime) -> Dict[str, float]:
    """
    计算总日消耗热量 (TDEE)
    
    基于用户的活动水平计算每日总消耗
    
    Returns:
        包含 bmr, tdee, target_calories 的字典
    """
    ctx = runtime.context
    
    # 计算 BMR
    bmr = calculate_bmr.invoke({}, runtime=runtime)
    
    # 活动系数
    activity_multipliers = {
        "sedentary": 1.2,      # 久坐
        "light": 1.375,        # 轻度活动
        "moderate": 1.55,      # 中度活动
        "active": 1.725,       # 高度活动
        "very_active": 1.9     # 极高活动
    }
    
    tdee = bmr * activity_multipliers.get(ctx.activity_level, 1.55)
    
    # 根据目标调整
    if ctx.goal == "lose_weight":
        target_calories = tdee - 500  # 每天减少500卡路里
    elif ctx.goal == "gain_muscle":
        target_calories = tdee + 300  # 每天增加300卡路里
    else:  # maintain
        target_calories = tdee
    
    return {
        "bmr": round(bmr, 2),
        "tdee": round(tdee, 2),
        "target_calories": round(target_calories, 2),
        "calorie_deficit": round(tdee - target_calories, 2) if ctx.goal == "lose_weight" else 0,
        "calorie_surplus": round(target_calories - tdee, 2) if ctx.goal == "gain_muscle" else 0
    }


@tool
def calculate_macros(runtime: ToolRuntime) -> Dict[str, Any]:
    """
    计算宏量营养素分配
    
    基于用户目标和热量需求计算蛋白质、碳水、脂肪分配
    
    Returns:
        宏量营养素分配信息
    """
    ctx = runtime.context
    
    # 获取目标热量
    tdee_info = calculate_tdee.invoke({}, runtime=runtime)
    target_calories = tdee_info["target_calories"]
    
    # 根据目标调整宏量营养素比例
    if ctx.goal == "lose_weight":
        # 减脂：高蛋白，中碳水，低脂肪
        protein_ratio = 0.35
        carbs_ratio = 0.40
        fats_ratio = 0.25
    elif ctx.goal == "gain_muscle":
        # 增肌：高蛋白，高碳水，中脂肪
        protein_ratio = 0.30
        carbs_ratio = 0.45
        fats_ratio = 0.25
    else:  # maintain
        # 维持：均衡分配
        protein_ratio = 0.25
        carbs_ratio = 0.45
        fats_ratio = 0.30
    
    # 计算克数（蛋白质和碳水：4卡/克，脂肪：9卡/克）
    protein_calories = target_calories * protein_ratio
    carbs_calories = target_calories * carbs_ratio
    fats_calories = target_calories * fats_ratio
    
    return {
        "target_calories": target_calories,
        "protein": {
            "grams": round(protein_calories / 4, 1),
            "calories": round(protein_calories, 1),
            "percentage": round(protein_ratio * 100, 1)
        },
        "carbs": {
            "grams": round(carbs_calories / 4, 1),
            "calories": round(carbs_calories, 1),
            "percentage": round(carbs_ratio * 100, 1)
        },
        "fats": {
            "grams": round(fats_calories / 9, 1),
            "calories": round(fats_calories, 1),
            "percentage": round(fats_ratio * 100, 1)
        }
    }


# ============================================================================
# 3. 用户偏好工具
# ============================================================================

@tool
def get_user_preferences(runtime: ToolRuntime) -> Dict[str, Any]:
    """
    获取用户偏好信息
    
    从上下文和数据库中获取用户的所有偏好设置
    
    Returns:
        用户偏好信息字典
    """
    ctx = runtime.context
    
    preferences = {
        "basic_info": {
            "goal": ctx.goal,
            "activity_level": ctx.activity_level,
            "timezone": ctx.timezone
        },
        "dietary_preferences": {
            "allergies": ctx.allergies,
            "dislikes": ctx.dislikes,
            "preferred_cuisines": ctx.preferred_cuisines,
            "dietary_restrictions": ctx.dietary_restrictions
        },
        "meal_preferences": {
            "preferred_meal_times": ctx.preferred_meal_times
        },
        "exercise_preferences": {
            "preferred_exercises": ctx.preferred_exercises,
            "exercise_limitations": ctx.exercise_limitations,
            "available_equipment": ctx.available_equipment
        }
    }
    
    # 如果有数据库会话，尝试获取更多偏好
    # if ctx.db_session:
    #     try:
    #         from app.repositories.preference_repository import PreferenceRepository
    #         pref_repo = PreferenceRepository(ctx.db_session)
    #         db_preferences = pref_repo.get_by_user_id(ctx.user_id)
    #         
    #         if db_preferences:
    #             preferences["database_preferences"] = {
    #                 "created_at": db_preferences.created_at.isoformat() if db_preferences.created_at else None,
    #                 "updated_at": db_preferences.updated_at.isoformat() if db_preferences.updated_at else None
    #             }
    #     except Exception as e:
    #         preferences["database_error"] = str(e)
    
    return preferences


@tool
def check_food_compatibility(runtime: ToolRuntime, food_name: str) -> Dict[str, Any]:
    """
    检查食物与用户偏好的兼容性
    
    Args:
        food_name: 食物名称
    
    Returns:
        兼容性检查结果
    """
    ctx = runtime.context
    
    result = {
        "food_name": food_name,
        "is_compatible": True,
        "issues": [],
        "recommendations": []
    }
    
    # 检查过敏
    for allergy in ctx.allergies:
        if allergy.lower() in food_name.lower():
            result["is_compatible"] = False
            result["issues"].append(f"包含过敏原：{allergy}")
    
    # 检查不喜欢的食物
    for dislike in ctx.dislikes:
        if dislike.lower() in food_name.lower():
            result["is_compatible"] = False
            result["issues"].append(f"用户不喜欢：{dislike}")
    
    # 检查饮食限制
    if "素食" in ctx.dietary_restrictions:
        meat_keywords = ["肉", "鸡", "牛", "猪", "鱼", "虾", "蟹"]
        for keyword in meat_keywords:
            if keyword in food_name:
                result["is_compatible"] = False
                result["issues"].append("不符合素食要求")
                break
    
    # 提供建议
    if not result["is_compatible"]:
        result["recommendations"].append("建议选择其他食物")
        if "过敏" in str(result["issues"]):
            result["recommendations"].append("请仔细检查食物成分")
    
    return result


# ============================================================================
# 4. 营养建议工具
# ============================================================================

@tool
def get_personalized_nutrition_advice(runtime: ToolRuntime, topic: str) -> str:
    """
    获取个性化营养建议
    
    基于用户的目标、偏好和身体数据提供定制化建议
    
    Args:
        topic: 咨询主题（如 protein, carbs, fats, meal_timing 等）
    
    Returns:
        个性化营养建议
    """
    ctx = runtime.context
    
    # 获取用户的宏量营养素需求
    macros = calculate_macros.invoke({}, runtime=runtime)
    
    advice_templates = {
        "protein": {
            "lose_weight": f"为了减脂，建议每天摄入 {macros['protein']['grams']}g 蛋白质。优质来源包括鸡胸肉、鱼类、蛋类、豆类。高蛋白有助于保持肌肉量和增加饱腹感。",
            "gain_muscle": f"为了增肌，建议每天摄入 {macros['protein']['grams']}g 蛋白质。在训练后30分钟内补充蛋白质效果最佳。",
            "maintain": f"为了维持体重，建议每天摄入 {macros['protein']['grams']}g 蛋白质。保持均衡摄入即可。"
        },
        "carbs": {
            "lose_weight": f"减脂期间建议每天摄入 {macros['carbs']['grams']}g 碳水化合物。选择复合碳水如燕麦、糙米、红薯，避免精制糖。",
            "gain_muscle": f"增肌期间建议每天摄入 {macros['carbs']['grams']}g 碳水化合物。训练前后适当增加碳水摄入。",
            "maintain": f"维持期间建议每天摄入 {macros['carbs']['grams']}g 碳水化合物。保持稳定摄入。"
        },
        "fats": {
            "lose_weight": f"减脂期间建议每天摄入 {macros['fats']['grams']}g 脂肪。选择健康脂肪如牛油果、坚果、橄榄油。",
            "gain_muscle": f"增肌期间建议每天摄入 {macros['fats']['grams']}g 脂肪。脂肪有助于激素合成。",
            "maintain": f"维持期间建议每天摄入 {macros['fats']['grams']}g 脂肪。保持均衡。"
        },
        "meal_timing": {
            "lose_weight": f"减脂建议：早餐 {ctx.preferred_meal_times['breakfast']}，午餐 {ctx.preferred_meal_times['lunch']}，晚餐 {ctx.preferred_meal_times['dinner']}。避免睡前3小时进食。",
            "gain_muscle": f"增肌建议：在你设定的时间规律进食，训练前后各加一次加餐。",
            "maintain": f"维持期间按你习惯的时间进食即可。"
        }
    }
    
    # 获取基础建议
    base_advice = advice_templates.get(topic, {}).get(ctx.goal, "请咨询专业营养师获取个性化建议。")
    
    # 添加个性化信息
    personalized_notes = []
    
    # 根据饮食限制添加建议
    if "素食" in ctx.dietary_restrictions and topic == "protein":
        personalized_notes.append("作为素食者，建议多摄入豆类、坚果、种子等植物蛋白。")
    
    # 根据过敏添加提醒
    if ctx.allergies and topic in ["protein", "general"]:
        personalized_notes.append(f"请注意避免过敏食物：{', '.join(ctx.allergies)}。")
    
    # 组合建议
    final_advice = base_advice
    if personalized_notes:
        final_advice += " " + " ".join(personalized_notes)
    
    return final_advice


# ============================================================================
# 5. 运动建议工具
# ============================================================================

@tool
def get_exercise_recommendations(runtime: ToolRuntime) -> Dict[str, Any]:
    """
    获取个性化运动建议
    
    基于用户的目标、活动水平、偏好和限制提供运动建议
    
    Returns:
        运动建议字典
    """
    ctx = runtime.context
    
    recommendations = {
        "goal": ctx.goal,
        "activity_level": ctx.activity_level,
        "weekly_plan": {},
        "exercise_types": [],
        "duration_per_session": 0,
        "frequency_per_week": 0,
        "notes": []
    }
    
    # 根据目标制定计划
    if ctx.goal == "lose_weight":
        recommendations["exercise_types"] = ["有氧运动", "力量训练"]
        recommendations["duration_per_session"] = 45
        recommendations["frequency_per_week"] = 5
        recommendations["weekly_plan"] = {
            "有氧运动": "3次/周，每次30-45分钟",
            "力量训练": "2次/周，每次30分钟"
        }
        recommendations["notes"].append("有氧运动有助于燃烧脂肪，力量训练保持肌肉量")
    
    elif ctx.goal == "gain_muscle":
        recommendations["exercise_types"] = ["力量训练", "少量有氧"]
        recommendations["duration_per_session"] = 60
        recommendations["frequency_per_week"] = 4
        recommendations["weekly_plan"] = {
            "力量训练": "4次/周，每次45-60分钟",
            "有氧运动": "1-2次/周，每次20分钟"
        }
        recommendations["notes"].append("重点进行复合动作训练，适度有氧保持心肺功能")
    
    else:  # maintain
        recommendations["exercise_types"] = ["有氧运动", "力量训练", "柔韧性训练"]
        recommendations["duration_per_session"] = 40
        recommendations["frequency_per_week"] = 4
        recommendations["weekly_plan"] = {
            "有氧运动": "2次/周，每次30分钟",
            "力量训练": "2次/周，每次30分钟",
            "柔韧性训练": "每天10分钟"
        }
        recommendations["notes"].append("保持均衡的运动组合")
    
    # 考虑用户偏好
    if ctx.preferred_exercises:
        recommendations["notes"].append(f"建议优先选择你喜欢的运动：{', '.join(ctx.preferred_exercises)}")
    
    # 考虑运动限制
    if ctx.exercise_limitations:
        recommendations["notes"].append(f"请注意运动限制：{', '.join(ctx.exercise_limitations)}")
    
    # 考虑可用器材
    if ctx.available_equipment:
        recommendations["notes"].append(f"可以利用现有器材：{', '.join(ctx.available_equipment)}")
    
    return recommendations


# ============================================================================
# 6. 工具列表（用于注册到 agent）
# ============================================================================

ENHANCED_TOOLS = [
    calculate_bmr,
    calculate_tdee,
    calculate_macros,
    get_user_preferences,
    check_food_compatibility,
    get_personalized_nutrition_advice,
    get_exercise_recommendations
]
