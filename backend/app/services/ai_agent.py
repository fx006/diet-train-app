"""
AI Agent service using LangChain 1.x and LangGraph 1.x

使用最新的 LangChain 1.1.0 和 LangGraph 1.0.4 API
这些版本是生产就绪的稳定版本，提供：
- 稳定的 API
- 更好的性能
- 完整的类型安全
- 持久化支持
"""
from typing import TypedDict, Annotated, List, Dict, Any, Optional
from datetime import date, datetime

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.tools import tool
from langchain_chroma import Chroma
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.repositories.plan_repository import PlanRepository
from app.repositories.preference_repository import PreferenceRepository
from app.services.vectorization_service import get_vectorization_service
from app.services.ai_prompts import (
    SYSTEM_PROMPT,
    PLAN_GENERATION_PROMPT,
    INTENT_UNDERSTANDING_PROMPT,
    format_user_preferences,
    format_historical_plans,
    format_similar_plans,
    format_knowledge
)


# Pydantic 模型用于结构化输出
class MealItem(BaseModel):
    """餐食项目"""
    name: str = Field(description="餐食名称")
    calories: float = Field(description="热量（卡路里）")
    items: List[str] = Field(description="食物列表")


class ExerciseItem(BaseModel):
    """运动项目"""
    name: str = Field(description="运动名称")
    duration: int = Field(description="时长（分钟）")
    calories: float = Field(description="消耗热量（卡路里）")


class DietPlan(BaseModel):
    """饮食训练计划"""
    date: str = Field(description="日期")
    meals: List[MealItem] = Field(description="餐食列表")
    exercises: List[ExerciseItem] = Field(description="运动列表")
    reasoning: str = Field(description="计划制定的理由和说明")


# ============================================================================
# 智能体工具定义
# ============================================================================

@tool
def get_user_preferences(user_id: Optional[int] = None) -> Dict[str, Any]:
    """
    获取用户偏好设置
    
    Args:
        user_id: 用户ID（可选，默认为1）
        
    Returns:
        用户偏好字典，包含目标、过敏食物、忌口等信息
    """
    try:
        db = next(get_db())
        repo = PreferenceRepository(db)
        
        # 默认使用用户ID 1
        if user_id is None:
            user_id = 1
        
        preferences = repo.get_by_user_id(user_id)
        
        if preferences:
            return {
                "goal": preferences.goal,
                "allergies": preferences.allergies,
                "dislikes": preferences.dislikes,
                "target_calories": preferences.target_calories,
                "activity_level": preferences.activity_level
            }
        else:
            return {
                "goal": "维持",
                "allergies": [],
                "dislikes": [],
                "target_calories": 2000,
                "activity_level": "中等"
            }
    except Exception as e:
        return {"error": f"获取用户偏好失败: {str(e)}"}


@tool
def get_historical_plans(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    获取历史计划（结构化查询）
    
    Args:
        start_date: 开始日期（YYYY-MM-DD格式）
        end_date: 结束日期（YYYY-MM-DD格式）
        limit: 返回的最大记录数
        
    Returns:
        历史计划列表
    """
    try:
        db = next(get_db())
        repo = PlanRepository(db)
        
        # 如果没有指定日期范围，获取最近的计划
        if not start_date and not end_date:
            # 获取最近的计划
            plans = repo.get_all()
            plans = sorted(plans, key=lambda x: x.date, reverse=True)[:limit]
        else:
            # 按日期范围查询
            if start_date:
                start = datetime.strptime(start_date, "%Y-%m-%d").date()
            else:
                start = date(2000, 1, 1)
            
            if end_date:
                end = datetime.strptime(end_date, "%Y-%m-%d").date()
            else:
                end = date.today()
            
            plans = []
            current = start
            while current <= end and len(plans) < limit:
                day_plans = repo.get_by_date(current)
                plans.extend(day_plans)
                current = date.fromordinal(current.toordinal() + 1)
        
        # 转换为字典格式
        result = []
        for plan in plans[:limit]:
            result.append({
                "id": plan.id,
                "date": plan.date.isoformat(),
                "type": plan.type,
                "name": plan.name,
                "calories": plan.calories,
                "duration": plan.duration,
                "completed": plan.completed
            })
        
        return result
    except Exception as e:
        return [{"error": f"获取历史计划失败: {str(e)}"}]


@tool
def search_similar_plans(query: str, n_results: int = 5) -> List[Dict[str, Any]]:
    """
    搜索相似计划（向量检索）
    
    Args:
        query: 搜索查询
        n_results: 返回的结果数量
        
    Returns:
        相似计划列表
    """
    try:
        vectorization_service = get_vectorization_service()
        results = vectorization_service.search_similar_plans(query, n_results)
        return results if results else []
    except Exception as e:
        return [{"error": f"搜索相似计划失败: {str(e)}"}]


@tool
def search_conversations(query: str, n_results: int = 3) -> List[str]:
    """
    搜索历史对话（向量检索）
    
    Args:
        query: 搜索查询
        n_results: 返回的结果数量
        
    Returns:
        相似对话列表
    """
    try:
        vectorization_service = get_vectorization_service()
        # 使用向量数据库搜索对话
        # 注意：这需要在 vectorization_service 中实现
        # 暂时返回空列表
        return []
    except Exception as e:
        return [f"搜索对话失败: {str(e)}"]


@tool
def search_knowledge(topic: str, knowledge_type: str = "both", n_results: int = 3) -> str:
    """
    搜索营养和运动知识库
    
    Args:
        topic: 搜索主题
        knowledge_type: 知识类型 ("nutrition", "exercise", "both")
        n_results: 返回的结果数量
        
    Returns:
        相关知识文本
    """
    try:
        vectorization_service = get_vectorization_service()
        
        results = []
        
        if knowledge_type in ["nutrition", "both"]:
            nutrition_knowledge = vectorization_service.get_nutrition_knowledge(
                topic, n_results
            )
            if nutrition_knowledge:
                results.append(f"营养知识：\n{nutrition_knowledge}")
        
        if knowledge_type in ["exercise", "both"]:
            exercise_knowledge = vectorization_service.get_exercise_knowledge(
                topic, n_results
            )
            if exercise_knowledge:
                results.append(f"运动知识：\n{exercise_knowledge}")
        
        return "\n\n".join(results) if results else "未找到相关知识"
    except Exception as e:
        return f"搜索知识失败: {str(e)}"


@tool
def calculate_nutrition(
    weight: float,
    height: float,
    age: int,
    gender: str,
    activity_level: str,
    goal: str
) -> Dict[str, Any]:
    """
    计算营养需求
    
    Args:
        weight: 体重（kg）
        height: 身高（cm）
        age: 年龄
        gender: 性别 ("male" 或 "female")
        activity_level: 活动水平 ("低", "中等", "高")
        goal: 目标 ("减脂", "增肌", "维持")
        
    Returns:
        营养需求字典，包含每日热量、蛋白质、碳水、脂肪等
    """
    try:
        # 计算基础代谢率 (BMR) - 使用 Mifflin-St Jeor 公式
        if gender.lower() in ["male", "男"]:
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            bmr = 10 * weight + 6.25 * height - 5 * age - 161
        
        # 根据活动水平调整
        activity_multipliers = {
            "低": 1.2,
            "中等": 1.55,
            "高": 1.9
        }
        multiplier = activity_multipliers.get(activity_level, 1.55)
        tdee = bmr * multiplier
        
        # 根据目标调整热量
        if goal == "减脂":
            target_calories = tdee - 500  # 每日减少500卡路里
            protein_ratio = 0.30  # 30% 蛋白质
            carb_ratio = 0.40     # 40% 碳水
            fat_ratio = 0.30      # 30% 脂肪
        elif goal == "增肌":
            target_calories = tdee + 300  # 每日增加300卡路里
            protein_ratio = 0.30
            carb_ratio = 0.50
            fat_ratio = 0.20
        else:  # 维持
            target_calories = tdee
            protein_ratio = 0.25
            carb_ratio = 0.50
            fat_ratio = 0.25
        
        # 计算宏量营养素（克）
        protein_grams = (target_calories * protein_ratio) / 4  # 1g蛋白质 = 4卡路里
        carb_grams = (target_calories * carb_ratio) / 4        # 1g碳水 = 4卡路里
        fat_grams = (target_calories * fat_ratio) / 9          # 1g脂肪 = 9卡路里
        
        return {
            "bmr": round(bmr, 1),
            "tdee": round(tdee, 1),
            "target_calories": round(target_calories, 1),
            "protein_grams": round(protein_grams, 1),
            "carb_grams": round(carb_grams, 1),
            "fat_grams": round(fat_grams, 1),
            "protein_ratio": protein_ratio,
            "carb_ratio": carb_ratio,
            "fat_ratio": fat_ratio
        }
    except Exception as e:
        return {"error": f"计算营养需求失败: {str(e)}"}


# ============================================================================
# LangGraph 状态定义
# ============================================================================

class AgentState(TypedDict):
    """智能体状态"""
    messages: Annotated[list, add_messages]  # 自动合并消息
    user_preferences: Dict[str, Any]
    historical_plans: List[Dict[str, Any]]
    retrieved_context: Dict[str, Any]
    generated_plan: Dict[str, Any]
    current_step: str


class DietTrainingAgent:
    """饮食训练计划 AI 智能体"""
    
    def __init__(self):
        """初始化智能体组件"""
        # 初始化 LLM（支持自定义API base）
        llm_kwargs = {
            "model": settings.openai_model_name,
            "temperature": 0.7,
            "api_key": settings.openai_api_key
        }
        if settings.openai_api_base:
            llm_kwargs["base_url"] = settings.openai_api_base
        
        self.llm = ChatOpenAI(**llm_kwargs)
        
        # 初始化 Embeddings（支持自定义API base和模型）
        embedding_kwargs = {
            "model": settings.openai_embedding_model,  # 使用配置的embedding模型
            "api_key": settings.openai_api_key
        }
        if settings.openai_api_base:
            embedding_kwargs["base_url"] = settings.openai_api_base
        
        self.embeddings = OpenAIEmbeddings(**embedding_kwargs)
        
        # 初始化向量存储
        self.vectorstore = Chroma(
            collection_name="diet_training",
            embedding_function=self.embeddings,
            persist_directory=settings.chroma_persist_directory
        )
        
        # 注册工具
        self.tools = [
            get_user_preferences,
            get_historical_plans,
            search_similar_plans,
            search_conversations,
            search_knowledge,
            calculate_nutrition
        ]
        
        # 将工具绑定到 LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # 创建智能体图
        self.agent = self._create_agent()
    
    def _call_tools(self, state: AgentState) -> AgentState:
        """调用工具节点"""
        messages = state["messages"]
        last_message = messages[-1]
        
        # 使用带工具的 LLM 处理消息
        response = self.llm_with_tools.invoke(messages)
        
        state["messages"].append(response)
        state["current_step"] = "tools_called"
        
        return state
    
    def _understand_intent(self, state: AgentState) -> AgentState:
        """理解用户意图"""
        messages = state["messages"]
        last_message = messages[-1].content if messages else ""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", INTENT_UNDERSTANDING_PROMPT),
            ("human", "{input}")
        ])
        
        chain = prompt | self.llm
        response = chain.invoke({"input": last_message})
        
        state["current_step"] = "intent_understood"
        state["messages"].append(AIMessage(content=response.content))
        
        return state
    
    def _retrieve_vector_context(self, state: AgentState) -> AgentState:
        """从向量数据库检索相关上下文（向量检索）"""
        messages = state["messages"]
        last_user_message = next(
            (m.content for m in reversed(messages) if isinstance(m, HumanMessage)),
            ""
        )
        
        # 语义搜索相似对话
        similar_conversations = self.vectorstore.similarity_search(
            last_user_message,
            k=3,
            filter={"type": "conversation"}
        )
        
        # 语义搜索相似计划
        similar_plans = self.vectorstore.similarity_search(
            last_user_message,
            k=3,
            filter={"type": "plan"}
        )
        
        # 搜索知识库
        knowledge = self.vectorstore.similarity_search(
            last_user_message,
            k=2,
            filter={"type": "knowledge"}
        )
        
        # 更新检索上下文
        if "retrieved_context" not in state:
            state["retrieved_context"] = {}
        
        state["retrieved_context"]["similar_conversations"] = [
            doc.page_content for doc in similar_conversations
        ]
        state["retrieved_context"]["similar_plans"] = [
            doc.page_content for doc in similar_plans
        ]
        state["retrieved_context"]["knowledge"] = [
            doc.page_content for doc in knowledge
        ]
        
        state["current_step"] = "vector_context_retrieved"
        
        return state
    
    def _retrieve_structured_data(self, state: AgentState) -> AgentState:
        """检索结构化数据（数据库查询）"""
        try:
            # 获取用户偏好
            user_prefs = get_user_preferences.invoke({})
            state["user_preferences"] = user_prefs
            
            # 获取最近的历史计划
            historical = get_historical_plans.invoke({"limit": 5})
            state["historical_plans"] = historical
            
            # 更新检索上下文
            if "retrieved_context" not in state:
                state["retrieved_context"] = {}
            
            state["retrieved_context"]["user_preferences"] = user_prefs
            state["retrieved_context"]["historical_plans"] = historical
            
            state["current_step"] = "structured_data_retrieved"
            
        except Exception as e:
            state["current_step"] = "error"
            state["messages"].append(
                AIMessage(content=f"检索结构化数据时出错：{str(e)}")
            )
        
        return state
    
    def _generate_plan(self, state: AgentState) -> AgentState:
        """生成饮食训练计划或普通对话响应"""
        messages = state["messages"]
        context = state["retrieved_context"]
        preferences = state["user_preferences"]
        historical = state["historical_plans"]
        
        last_user_message = next(
            (m.content for m in reversed(messages) if isinstance(m, HumanMessage)),
            ""
        )
        
        # 判断用户是否需要生成计划
        plan_keywords = ["计划", "饮食", "餐食", "运动", "锻炼", "健身", "减脂", "增肌", "生成", "帮我"]
        needs_plan = any(keyword in last_user_message for keyword in plan_keywords)
        
        if needs_plan:
            # 生成结构化计划
            try:
                parser = JsonOutputParser(pydantic_object=DietPlan)
                
                # 格式化上下文信息
                formatted_preferences = format_user_preferences(preferences)
                formatted_historical = format_historical_plans(historical)
                formatted_similar = format_similar_plans(context.get("similar_plans", []))
                formatted_knowledge = format_knowledge(context.get("knowledge", []))
                
                # 构建提示词
                prompt = ChatPromptTemplate.from_messages([
                    ("system", PLAN_GENERATION_PROMPT),
                    ("human", "{input}")
                ])
                
                chain = prompt | self.llm | parser
                
                result = chain.invoke({
                    "input": last_user_message,
                    "user_preferences": formatted_preferences,
                    "historical_plans": formatted_historical,
                    "similar_plans": formatted_similar,
                    "knowledge": formatted_knowledge,
                    "format_instructions": parser.get_format_instructions()
                })
                
                state["generated_plan"] = result
                state["current_step"] = "plan_generated"
                
                # 添加 AI 响应消息
                response_text = f"我已经为您生成了饮食训练计划。\n\n{result.get('reasoning', '')}"
                state["messages"].append(AIMessage(content=response_text))
                
            except Exception as e:
                state["current_step"] = "error"
                state["messages"].append(
                    AIMessage(content=f"生成计划时出错：{str(e)}")
                )
        else:
            # 普通对话响应
            try:
                prompt = ChatPromptTemplate.from_messages([
                    ("system", SYSTEM_PROMPT),
                    ("human", "{input}")
                ])
                
                chain = prompt | self.llm
                
                response = chain.invoke({"input": last_user_message})
                
                state["current_step"] = "response_generated"
                state["messages"].append(AIMessage(content=response.content))
                
            except Exception as e:
                state["current_step"] = "error"
                state["messages"].append(
                    AIMessage(content=f"生成响应时出错：{str(e)}")
                )
        
        return state
    
    def _validate_plan(self, state: AgentState) -> AgentState:
        """验证计划的合理性"""
        plan = state["generated_plan"]
        
        if not plan:
            state["current_step"] = "validation_failed"
            return state
        
        # 验证热量平衡
        total_intake = sum(meal.get("calories", 0) for meal in plan.get("meals", []))
        total_burned = sum(ex.get("calories", 0) for ex in plan.get("exercises", []))
        
        # 基本验证规则
        if total_intake < 1000 or total_intake > 5000:
            state["messages"].append(
                AIMessage(content="警告：总热量摄入可能不合理，请调整。")
            )
        
        if total_burned > total_intake * 0.5:
            state["messages"].append(
                AIMessage(content="提示：运动消耗较大，注意补充能量。")
            )
        
        state["current_step"] = "plan_validated"
        
        return state
    
    def _format_response(self, state: AgentState) -> AgentState:
        """格式化响应"""
        plan = state["generated_plan"]
        
        if not plan:
            state["current_step"] = "response_formatted"
            return state
        
        # 格式化计划为易读的文本
        formatted_text = f"📅 日期: {plan.get('date', '今天')}\n\n"
        
        # 格式化餐食
        if plan.get("meals"):
            formatted_text += "🍽️ 餐食安排:\n"
            for i, meal in enumerate(plan.get("meals", []), 1):
                formatted_text += f"{i}. {meal.get('name', '未命名餐食')}\n"
                formatted_text += f"   热量: {meal.get('calories', 0)}卡路里\n"
                if meal.get("items"):
                    formatted_text += f"   食物: {', '.join(meal.get('items', []))}\n"
                formatted_text += "\n"
        
        # 格式化运动
        if plan.get("exercises"):
            formatted_text += "💪 运动安排:\n"
            for i, exercise in enumerate(plan.get("exercises", []), 1):
                formatted_text += f"{i}. {exercise.get('name', '未命名运动')}\n"
                formatted_text += f"   时长: {exercise.get('duration', 0)}分钟\n"
                formatted_text += f"   消耗: {exercise.get('calories', 0)}卡路里\n\n"
        
        # 添加理由
        if plan.get("reasoning"):
            formatted_text += f"💡 计划说明:\n{plan.get('reasoning')}\n"
        
        # 更新最后一条 AI 消息或添加新消息
        if state["messages"] and isinstance(state["messages"][-1], AIMessage):
            state["messages"][-1] = AIMessage(content=formatted_text)
        else:
            state["messages"].append(AIMessage(content=formatted_text))
        
        state["current_step"] = "response_formatted"
        
        return state
    
    def _store_to_vector_db(self, state: AgentState) -> AgentState:
        """将对话和计划存储到向量数据库"""
        from langchain_core.documents import Document
        
        # 存储对话
        messages = state["messages"]
        for msg in messages[-2:]:  # 只存储最近的对话
            if isinstance(msg, (HumanMessage, AIMessage)):
                doc = Document(
                    page_content=msg.content,
                    metadata={
                        "role": "user" if isinstance(msg, HumanMessage) else "assistant",
                        "type": "conversation",
                        "timestamp": date.today().isoformat()
                    }
                )
                self.vectorstore.add_documents([doc])
        
        # 存储生成的计划
        plan = state["generated_plan"]
        if plan:
            content = f"日期: {plan.get('date', '')}\n"
            content += f"餐食: {', '.join([m.get('name', '') for m in plan.get('meals', [])])}\n"
            content += f"运动: {', '.join([e.get('name', '') for e in plan.get('exercises', [])])}\n"
            content += f"理由: {plan.get('reasoning', '')}"
            
            doc = Document(
                page_content=content,
                metadata={
                    "type": "plan",
                    "date": plan.get("date", ""),
                    "timestamp": date.today().isoformat()
                }
            )
            self.vectorstore.add_documents([doc])
        
        state["current_step"] = "stored"
        
        return state
    
    def _execute_tools(self, state: AgentState) -> AgentState:
        """执行工具调用"""
        messages = state["messages"]
        last_message = messages[-1]
        
        # 检查是否有工具调用
        if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
            return state
        
        # 创建工具映射
        tool_map = {tool.name: tool for tool in self.tools}
        
        # 执行每个工具调用
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            if tool_name in tool_map:
                try:
                    # 调用工具
                    tool_result = tool_map[tool_name].invoke(tool_args)
                    
                    # 添加工具结果消息
                    tool_message = ToolMessage(
                        content=str(tool_result),
                        tool_call_id=tool_call["id"]
                    )
                    state["messages"].append(tool_message)
                except Exception as e:
                    # 添加错误消息
                    error_message = ToolMessage(
                        content=f"工具执行错误: {str(e)}",
                        tool_call_id=tool_call["id"]
                    )
                    state["messages"].append(error_message)
        
        state["current_step"] = "tools_executed"
        return state
    
    def _should_continue(self, state: AgentState) -> str:
        """判断是否需要继续调用工具"""
        messages = state["messages"]
        last_message = messages[-1]
        
        # 如果最后一条消息包含工具调用，继续执行工具
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        
        # 否则继续到下一步
        return "continue"
    
    def _create_agent(self) -> Any:
        """创建 LangGraph 智能体（RAG 流程）"""
        workflow = StateGraph(AgentState)
        
        # 添加节点 - RAG 流程
        workflow.add_node("call_tools", self._call_tools)
        workflow.add_node("tools", self._execute_tools)
        workflow.add_node("understand_intent", self._understand_intent)
        workflow.add_node("retrieve_vector_context", self._retrieve_vector_context)
        workflow.add_node("retrieve_structured_data", self._retrieve_structured_data)
        workflow.add_node("generate_plan", self._generate_plan)
        workflow.add_node("validate_plan", self._validate_plan)
        workflow.add_node("format_response", self._format_response)
        workflow.add_node("store_to_vector_db", self._store_to_vector_db)
        
        # 添加边 - 构建 RAG 工作流
        workflow.add_edge(START, "call_tools")
        
        # 条件边：根据是否需要调用工具决定下一步
        workflow.add_conditional_edges(
            "call_tools",
            self._should_continue,
            {
                "tools": "tools",
                "continue": "understand_intent"
            }
        )
        
        # 工具执行后返回到 call_tools
        workflow.add_edge("tools", "call_tools")
        
        # RAG 检索流程
        workflow.add_edge("understand_intent", "retrieve_vector_context")
        workflow.add_edge("retrieve_vector_context", "retrieve_structured_data")
        
        # 生成和验证流程
        workflow.add_edge("retrieve_structured_data", "generate_plan")
        workflow.add_edge("generate_plan", "validate_plan")
        workflow.add_edge("validate_plan", "format_response")
        
        # 存储和结束
        workflow.add_edge("format_response", "store_to_vector_db")
        workflow.add_edge("store_to_vector_db", END)
        
        # 编译图
        return workflow.compile()
    
    def generate_plan(
        self,
        user_input: str,
        user_preferences: Dict[str, Any],
        historical_plans: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成饮食训练计划
        
        Args:
            user_input: 用户输入
            user_preferences: 用户偏好
            historical_plans: 历史计划
            
        Returns:
            生成的计划
        """
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "user_preferences": user_preferences or {},
            "historical_plans": historical_plans or [],
            "retrieved_context": {},
            "generated_plan": {},
            "current_step": "start"
        }
        
        # 调用智能体
        result = self.agent.invoke(initial_state)
        
        return {
            "plan": result["generated_plan"],
            "messages": [
                {"role": "user" if isinstance(m, HumanMessage) else "assistant", "content": m.content}
                for m in result["messages"]
            ]
        }
    
    async def generate_plan_stream(
        self,
        user_input: str,
        user_preferences: Dict[str, Any]
    ):
        """
        流式生成计划
        
        Args:
            user_input: 用户输入
            user_preferences: 用户偏好
            
        Yields:
            生成的内容块
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个饮食训练计划助手。用户偏好：{preferences}"),
            ("human", "{input}")
        ])
        
        chain = prompt | self.llm
        
        async for chunk in chain.astream({
            "input": user_input,
            "preferences": user_preferences
        }):
            if chunk.content:
                yield chunk.content


# ============================================================================
# 全局智能体实例
# ============================================================================

_agent_instance: Optional[DietTrainingAgent] = None


def get_ai_agent() -> DietTrainingAgent:
    """
    获取AI智能体实例（单例模式）
    
    Returns:
        DietTrainingAgent 实例
    """
    global _agent_instance
    
    if _agent_instance is None:
        _agent_instance = DietTrainingAgent()
    
    return _agent_instance
