"""
AI Agent service using LangChain 1.x create_agent API

基于 LangChain 1.1.0 官方推荐的 create_agent API 重构
参考官方文档: https://docs.langchain.com/oss/python/langchain/quickstart

主要改进:
- 使用 create_agent 简化智能体创建
- 使用 ToolRuntime[Context] 自动注入用户上下文
- 使用 ToolStrategy 确保结构化输出
- 使用 InMemorySaver 自动管理记忆
- 使用 init_chat_model 标准化模型配置
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import date

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool, ToolRuntime
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents.structured_output import ToolStrategy
from pydantic import BaseModel, Field
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

from app.config import settings


# ============================================================================
# 1. 用户上下文定义（运行时注入）
# ============================================================================

@dataclass
class UserContext:
    """
    用户上下文 - 自动注入到工具中
    使用 ToolRuntime[UserContext] 模式，工具可以自动访问这些数据
    """
    user_id: str
    age: int
    gender: str  # male/female
    weight: float  # kg
    height: float  # cm
    goal: str  # lose_weight, gain_muscle, maintain
    activity_level: str  # sedentary, light, moderate, active, very_active
    allergies: List[str] = None  # 过敏食物
    dislikes: List[str] = None  # 不喜欢的食物
    
    def __post_init__(self):
        if self.allergies is None:
            self.allergies = []
        if self.dislikes is None:
            self.dislikes = []


# ============================================================================
# 2. 结构化输出模型（Pydantic）
# ============================================================================

class MealPlan(BaseModel):
    """餐食计划"""
    meal_time: str = Field(description="用餐时间，如'早餐'、'午餐'、'晚餐'、'加餐'")
    foods: List[str] = Field(description="食物列表")
    total_calories: int = Field(description="总热量（卡路里）")
    protein: int = Field(description="蛋白质（克）")
    carbs: int = Field(description="碳水化合物（克）")
    fats: int = Field(description="脂肪（克）")


class ExercisePlan(BaseModel):
    """运动计划"""
    name: str = Field(description="运动名称")
    duration: int = Field(description="时长（分钟）")
    calories_burned: int = Field(description="消耗热量（卡路里）")
    intensity: str = Field(description="强度：低、中、高")


class DailyPlan(BaseModel):
    """每日计划 - 结构化输出格式"""
    date: str = Field(description="日期 YYYY-MM-DD")
    meals: List[MealPlan] = Field(description="餐食列表")
    exercises: List[ExercisePlan] = Field(description="运动列表")
    total_calories_intake: int = Field(description="总热量摄入")
    total_calories_burned: int = Field(description="总热量消耗")
    net_calories: int = Field(description="净热量（摄入-消耗）")
    notes: str = Field(description="备注和建议")


# ============================================================================
# 3. 工具定义（使用 @tool 装饰器）
# ============================================================================

@tool
def calculate_bmr(weight: float, height: float, age: int, gender: str) -> float:
    """
    计算基础代谢率 (BMR)
    使用 Mifflin-St Jeor 公式
    
    Args:
        weight: 体重（公斤）
        height: 身高（厘米）
        age: 年龄
        gender: 性别（male/female）
    
    Returns:
        基础代谢率（卡路里/天）
    """
    if gender.lower() == "male":
        return 10 * weight + 6.25 * height - 5 * age + 5
    else:
        return 10 * weight + 6.25 * height - 5 * age - 161


@tool
def calculate_daily_calories(runtime: ToolRuntime) -> Dict[str, Any]:
    """
    根据用户信息计算每日热量需求
    
    使用 ToolRuntime 自动获取用户上下文
    无需手动传递用户数据
    
    Returns:
        包含 bmr, tdee, target_calories 等信息的字典
    """
    ctx = runtime.context
    
    # 计算 BMR
    bmr = calculate_bmr.invoke({
        "weight": ctx.weight,
        "height": ctx.height,
        "age": ctx.age,
        "gender": ctx.gender
    })
    
    # 活动系数
    activity_multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9
    }
    
    tdee = bmr * activity_multipliers.get(ctx.activity_level, 1.55)
    
    # 根据目标调整
    if ctx.goal == "lose_weight":
        target_calories = tdee - 500
    elif ctx.goal == "gain_muscle":
        target_calories = tdee + 300
    else:  # maintain
        target_calories = tdee
    
    return {
        "bmr": round(bmr, 2),
        "tdee": round(tdee, 2),
        "target_calories": round(target_calories, 2),
        "protein_grams": int(target_calories * 0.30 / 4),
        "carbs_grams": int(target_calories * 0.40 / 4),
        "fats_grams": int(target_calories * 0.30 / 9)
    }


@tool
def get_nutrition_advice(food_type: str) -> str:
    """
    获取营养建议
    
    Args:
        food_type: 食物类型或营养问题（如 protein, carbs, fats, breakfast 等）
    
    Returns:
        营养建议文本
    """
    advice_db = {
        "protein": "优质蛋白质来源包括鸡胸肉、鱼类、蛋类、豆类。建议每公斤体重摄入1.6-2.2克蛋白质。",
        "carbs": "选择复合碳水化合物如燕麦、糙米、红薯，避免精制糖和白面包。",
        "fats": "健康脂肪来源包括牛油果、坚果、橄榄油、深海鱼类。",
        "breakfast": "早餐应包含蛋白质、复合碳水和健康脂肪，如燕麦+蛋白粉+坚果。",
        "lunch": "午餐应该是一天中最丰盛的一餐，包含充足的蛋白质和蔬菜。",
        "dinner": "晚餐应该清淡，避免过多碳水化合物，以蛋白质和蔬菜为主。",
        "hydration": "每天至少饮水2-3升，运动时需要额外补充。",
        "snack": "加餐选择坚果、水果、酸奶等健康食品，避免高糖零食。"
    }
    
    return advice_db.get(food_type.lower(), "请咨询专业营养师获取个性化建议。")


@tool
def get_user_preferences(runtime: ToolRuntime) -> Dict[str, Any]:
    """
    获取用户偏好信息
    
    使用 ToolRuntime 自动访问用户上下文
    
    Returns:
        用户偏好信息字典
    """
    ctx = runtime.context
    
    return {
        "goal": ctx.goal,
        "allergies": ctx.allergies,
        "dislikes": ctx.dislikes,
        "activity_level": ctx.activity_level
    }


# ============================================================================
# 4. 饮食训练智能体类
# ============================================================================

class DietTrainingAgentV2:
    """
    饮食训练计划 AI 智能体 V2
    
    使用 LangChain 1.x 的 create_agent API 重构
    主要改进：
    - 更简洁的代码
    - 自动的上下文管理
    - 自动的记忆管理
    - 结构化输出保证
    """
    
    def __init__(self):
        """初始化智能体"""
        
        # 系统提示词
        self.system_prompt = """你是一个专业的饮食训练计划助手。

你有以下工具可以使用：
- calculate_daily_calories: 计算用户的每日热量需求
- get_nutrition_advice: 获取营养建议
- get_user_preferences: 获取用户偏好信息

请根据用户的个人信息和目标，生成科学合理的饮食训练计划。

确保计划：
1. 符合用户的热量需求
2. 营养均衡（蛋白质30%、碳水40%、脂肪30%）
3. 实用可行
4. 避免用户的过敏食物
5. 避免用户不喜欢的食物
6. 包含详细的食物选择和运动安排
7. 运动强度适中，循序渐进

生成计划时：
- 早餐应该丰富营养
- 午餐应该是最丰盛的一餐
- 晚餐应该清淡
- 可以包含1-2次健康加餐
- 运动安排要考虑用户的活动水平
- 提供具体的食物名称和份量建议"""
        
        # 初始化模型（使用 init_chat_model）
        # 支持自定义API base和模型名称
        model_kwargs = {
            "temperature": 0.7,
            "timeout": 30,
            "max_tokens": 2000,
        }
        
        # 如果设置了自定义API base，添加到配置中
        if settings.openai_api_base:
            model_kwargs["base_url"] = settings.openai_api_base
        
        # 如果设置了API key，添加到配置中
        if settings.openai_api_key:
            model_kwargs["api_key"] = settings.openai_api_key
        
        self.model = init_chat_model(
            settings.openai_model_name,  # 使用配置的模型名称
            **model_kwargs
        )
        
        # 工具列表
        self.tools = [
            calculate_daily_calories,
            get_nutrition_advice,
            get_user_preferences
        ]
        
        # 设置记忆（使用 InMemorySaver）
        self.checkpointer = InMemorySaver()
        
        # 创建 agent（使用 create_agent）
        self.agent = create_agent(
            model=self.model,
            tools=self.tools,
            system_prompt=self.system_prompt,
            context_schema=UserContext,
            response_format=ToolStrategy(DailyPlan),  # 结构化输出
            checkpointer=self.checkpointer
        )
    
    def generate_plan(
        self,
        user_request: str,
        user_context: UserContext,
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成饮食训练计划
        
        Args:
            user_request: 用户请求
            user_context: 用户上下文信息
            thread_id: 对话线程 ID（用于记忆管理）
            
        Returns:
            包含结构化计划的响应
        """
        # 如果没有提供 thread_id，使用 user_id
        if thread_id is None:
            thread_id = f"user_{user_context.user_id}"
        
        # 配置（用于记忆管理）
        config = {"configurable": {"thread_id": thread_id}}
        
        # 调用 agent
        response = self.agent.invoke(
            {"messages": [{"role": "user", "content": user_request}]},
            config=config,
            context=user_context
        )
        
        return {
            "structured_response": response.get("structured_response"),
            "messages": response.get("messages", []),
            "thread_id": thread_id
        }
    
    def continue_conversation(
        self,
        user_message: str,
        user_context: UserContext,
        thread_id: str
    ) -> Dict[str, Any]:
        """
        继续对话（利用记忆功能）
        
        Args:
            user_message: 用户消息
            user_context: 用户上下文
            thread_id: 对话线程 ID
            
        Returns:
            响应
        """
        config = {"configurable": {"thread_id": thread_id}}
        
        response = self.agent.invoke(
            {"messages": [{"role": "user", "content": user_message}]},
            config=config,
            context=user_context
        )
        
        return {
            "structured_response": response.get("structured_response"),
            "messages": response.get("messages", []),
            "thread_id": thread_id
        }
    
    async def stream_plan_generation(
        self,
        user_request: str,
        user_context: UserContext,
        thread_id: Optional[str] = None
    ):
        """
        流式生成计划（实时显示生成过程）
        
        Args:
            user_request: 用户请求
            user_context: 用户上下文
            thread_id: 对话线程 ID
            
        Yields:
            流式响应块
        """
        if thread_id is None:
            thread_id = f"user_{user_context.user_id}"
        
        config = {"configurable": {"thread_id": thread_id}}
        
        # 使用 astream 流式输出
        async for chunk in self.agent.astream(
            {"messages": [{"role": "user", "content": user_request}]},
            config=config,
            context=user_context
        ):
            yield chunk


# ============================================================================
# 5. 工厂函数
# ============================================================================

def create_diet_agent() -> DietTrainingAgentV2:
    """创建饮食训练智能体的工厂函数"""
    return DietTrainingAgentV2()


# ============================================================================
# 6. 使用示例
# ============================================================================

async def example_usage():
    """使用示例 - 展示如何使用新的智能体"""
    
    # 1. 创建 agent
    agent = create_diet_agent()
    
    # 2. 定义用户上下文
    user_ctx = UserContext(
        user_id="user_123",
        age=30,
        gender="male",
        weight=75.0,
        height=175.0,
        goal="lose_weight",
        activity_level="moderate",
        allergies=["花生"],
        dislikes=["西兰花"]
    )
    
    # 3. 生成计划
    print("=== 生成饮食训练计划 ===")
    result = agent.generate_plan(
        "请为我生成一个减脂的饮食训练计划",
        user_ctx
    )
    
    print(f"结构化响应: {result['structured_response']}")
    print(f"Thread ID: {result['thread_id']}")
    
    # 4. 继续对话（会记住之前的内容）
    print("\n=== 继续对话 ===")
    follow_up = agent.continue_conversation(
        "能否调整一下早餐的安排？我想要更多蛋白质。",
        user_ctx,
        thread_id=result['thread_id']
    )
    
    print(f"后续响应: {follow_up['structured_response']}")
    
    # 5. 流式生成
    print("\n=== 流式生成 ===")
    async for chunk in agent.stream_plan_generation(
        "生成明天的计划",
        user_ctx
    ):
        if chunk.get("messages"):
            latest_msg = chunk["messages"][-1]
            if hasattr(latest_msg, 'content') and latest_msg.content:
                print(f"流式: {latest_msg.content[:100]}...")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
