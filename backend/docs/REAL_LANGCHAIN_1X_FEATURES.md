# 基于真实官方文档的 LangChain 1.x 特性分析

> 本文档基于 LangChain 官方文档（2025年版本）
> 参考: https://docs.langchain.com/oss/python/langchain/

## 📋 官方文档核心内容

### 🎯 LangChain 1.x 的真实变化

根据官方文档，LangChain 1.x 带来了以下**真实的**重大变化：

1. **API 完全稳定** - 1.x 标志着生产就绪，不再有破坏性变更
2. **简化的架构** - 所有旧的 chains 和 agents 被单一的 `create_agent` 替代
3. **基于 LangGraph** - 所有 agents 都构建在 LangGraph 之上
4. **标准化消息格式** - 支持多模态、推理块、服务器端工具调用

### 🔥 真实的核心 API

## 1. `create_agent` - 创建智能体

**官方 API**：
```python
from langchain.agents import create_agent

agent = create_agent(
    model="claude-sonnet-4-5-20250929",
    tools=[get_weather],
    system_prompt="You are a helpful assistant",
)
```

**关键参数**：
- `model`: 模型标识符或模型实例
- `tools`: 工具列表
- `system_prompt`: 系统提示词
- `context_schema`: 运行时上下文模式
- `response_format`: 结构化输出策略
- `checkpointer`: 记忆管理器

**应用到我们的项目**：
```python
agent = create_agent(
    model="gpt-4o",
    tools=[calculate_daily_calories, get_nutrition_advice],
    system_prompt="你是专业的营养师和健身教练...",
    context_schema=UserContext,
    response_format=ToolStrategy(DailyPlan),
    checkpointer=InMemorySaver()
)
```

## 2. `init_chat_model` - 初始化模型

**官方 API**：
```python
from langchain.chat_models import init_chat_model

model = init_chat_model(
    "claude-sonnet-4-5-20250929",
    temperature=0.5,
    timeout=10,
    max_tokens=1000
)
```

**支持的参数**：
- `model`: 模型名称
- `temperature`: 温度参数
- `timeout`: 超时时间
- `max_tokens`: 最大 token 数
- `max_retries`: 最大重试次数

**应用到我们的项目**：
```python
model = init_chat_model(
    "gpt-4o",
    temperature=0.7,
    timeout=30,
    max_tokens=2000
)
```

## 3. `@tool` 装饰器 - 定义工具

**官方 API**：
```python
from langchain.tools import tool

@tool
def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"
```

**关键特性**：
- 自动从函数签名生成工具模式
- 支持类型提示
- 文档字符串作为工具描述

**应用到我们的项目**：
```python
@tool
def calculate_bmr(weight: float, height: float, age: int, gender: str) -> float:
    """计算基础代谢率 (BMR)"""
    if gender.lower() == "male":
        return 10 * weight + 6.25 * height - 5 * age + 5
    else:
        return 10 * weight + 6.25 * height - 5 * age - 161
```

## 4. `ToolRuntime[Context]` - 运行时上下文

**官方模式**：
```python
from dataclasses import dataclass
from langchain.tools import tool, ToolRuntime

@dataclass
class Context:
    user_id: str

@tool
def get_user_location(runtime: ToolRuntime[Context]) -> str:
    """Retrieve user information based on user ID."""
    user_id = runtime.context.user_id
    return "Florida" if user_id == "1" else "SF"
```

**应用到我们的项目**：
```python
@dataclass
class UserContext:
    user_id: str
    age: int
    gender: str
    weight: float
    height: float
    goal: str
    activity_level: str

@tool
def calculate_daily_calories(runtime: ToolRuntime[UserContext]) -> Dict[str, float]:
    """根据用户信息计算每日热量需求"""
    ctx = runtime.context
    # 使用 ctx.weight, ctx.height 等
    ...
```

## 5. 结构化输出策略

**官方支持两种策略**：

### ToolStrategy（推荐）

使用人工工具调用生成结构化输出，适用于所有支持工具调用的模型：

```python
from langchain.agents.structured_output import ToolStrategy
from pydantic import BaseModel

class ResponseFormat(BaseModel):
    punny_response: str
    weather_conditions: str | None = None

agent = create_agent(
    model=model,
    tools=tools,
    response_format=ToolStrategy(ResponseFormat),
)
```

### ProviderStrategy

使用模型提供商的原生结构化输出，更可靠但仅适用于支持的提供商（如 OpenAI）：

```python
from langchain.agents.structured_output import ProviderStrategy

agent = create_agent(
    model="gpt-4o",
    response_format=ProviderStrategy(ResponseFormat)
)
```

**应用到我们的项目**：
```python
class DailyPlan(BaseModel):
    date: str
    meals: List[MealPlan]
    exercises: List[ExercisePlan]
    total_calories_intake: int
    total_calories_burned: int
    net_calories: int
    notes: str

agent = create_agent(
    model=model,
    tools=tools,
    response_format=ToolStrategy(DailyPlan)
)
```

## 6. 内存管理 - `InMemorySaver`

**官方 API**：
```python
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()

agent = create_agent(
    model=model,
    tools=tools,
    checkpointer=checkpointer
)

# 使用线程 ID 进行对话
config = {"configurable": {"thread_id": "user_123"}}
response = agent.invoke(messages, config=config)
```

**应用到我们的项目**：
```python
checkpointer = InMemorySaver()

agent = create_agent(
    model=model,
    tools=tools,
    checkpointer=checkpointer
)

# 第一次对话
config = {"configurable": {"thread_id": f"user_{user_id}"}}
plan = agent.invoke(
    {"messages": [{"role": "user", "content": "生成减脂计划"}]},
    config=config,
    context=user_context
)

# 后续对话会记住之前的内容
adjustment = agent.invoke(
    {"messages": [{"role": "user", "content": "我不喜欢西兰花"}]},
    config=config,  # 同一个 thread_id
    context=user_context
)
```

## 7. 流式输出

**官方 API**：
```python
for chunk in agent.stream(messages, stream_mode="values"):
    latest_message = chunk["messages"][-1]
    if latest_message.content:
        print(f"Agent: {latest_message.content}")
```

**异步流式**：
```python
async for chunk in agent.astream(messages):
    if chunk.get("messages"):
        latest_msg = chunk["messages"][-1]
        if hasattr(latest_msg, 'content') and latest_msg.content:
            print(f"Agent: {latest_msg.content}")
```

**应用到我们的项目**：
```python
async def stream_plan_to_frontend(user_request, user_context):
    async for chunk in agent.astream(
        {"messages": [{"role": "user", "content": user_request}]},
        config={"configurable": {"thread_id": "user_123"}},
        context=user_context
    ):
        # 发送到前端
        yield f"data: {json.dumps(chunk)}\\n\\n"
```

## 🎯 针对饮食训练项目的具体应用

### 完整示例（基于官方 Quickstart）

```python
from dataclasses import dataclass
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool, ToolRuntime
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents.structured_output import ToolStrategy
from pydantic import BaseModel, Field

# 1. 定义上下文
@dataclass
class UserContext:
    user_id: str
    age: int
    gender: str
    weight: float
    height: float
    goal: str
    activity_level: str

# 2. 定义结构化输出
class DailyPlan(BaseModel):
    date: str = Field(description="日期 YYYY-MM-DD")
    meals: List[dict] = Field(description="餐食列表")
    exercises: List[dict] = Field(description="运动列表")
    notes: str = Field(description="备注和建议")

# 3. 定义工具
@tool
def calculate_daily_calories(runtime: ToolRuntime[UserContext]) -> dict:
    """根据用户信息计算每日热量需求"""
    ctx = runtime.context
    # 计算逻辑...
    return {"target_calories": 2000, "protein": 150, ...}

@tool
def get_nutrition_advice(food_type: str) -> str:
    """获取营养建议"""
    return f"关于 {food_type} 的营养建议..."

# 4. 初始化模型
model = init_chat_model(
    "gpt-4o",
    temperature=0.7,
    timeout=30,
    max_tokens=2000
)

# 5. 创建 agent
agent = create_agent(
    model=model,
    tools=[calculate_daily_calories, get_nutrition_advice],
    system_prompt="你是专业的营养师和健身教练...",
    context_schema=UserContext,
    response_format=ToolStrategy(DailyPlan),
    checkpointer=InMemorySaver()
)

# 6. 使用 agent
user_ctx = UserContext(
    user_id="user_123",
    age=30,
    gender="male",
    weight=75.0,
    height=175.0,
    goal="lose_weight",
    activity_level="moderate"
)

config = {"configurable": {"thread_id": "session_1"}}

response = agent.invoke(
    {"messages": [{"role": "user", "content": "生成减脂计划"}]},
    config=config,
    context=user_ctx
)

print(response['structured_response'])
# DailyPlan(date='2025-12-02', meals=[...], exercises=[...], notes='...')
```

## 📊 官方文档中的其他重要特性

### 1. 工具调用

- **并行工具调用**: 模型可以同时调用多个工具
- **强制工具调用**: 可以强制模型使用特定工具
- **流式工具调用**: 工具调用可以流式返回

### 2. 多模态支持

模型可以处理图片、音频、视频等多模态输入：

```python
response = agent.invoke({
    "messages": [{
        "role": "user",
        "content": [
            {"type": "text", "text": "分析这个食物的营养成分"},
            {"type": "image", "image_url": {"url": "data:image/jpeg;base64,..."}}
        ]
    }]
})
```

### 3. 推理过程可视化

某些模型支持显示推理步骤：

```python
for chunk in model.stream("为什么推荐这个饮食计划？"):
    reasoning_steps = [r for r in chunk.content_blocks if r["type"] == "reasoning"]
    if reasoning_steps:
        print(f"推理: {reasoning_steps[0]['reasoning']}")
```

### 4. 服务器端工具

某些提供商支持服务器端工具（如网络搜索）：

```python
tool = {"type": "web_search"}
model_with_tools = model.bind_tools([tool])

response = model_with_tools.invoke("搜索最新的营养研究报告")
```

## 🔧 依赖版本（基于官方文档）

```txt
langchain==1.1.0
langchain-core==1.1.0
langchain-community==0.4.1  # 注意：不是 1.x
langgraph==1.0.4
langchain-openai==1.1.0
langchain-anthropic==1.1.0
```

## 📋 实施建议

### 第一阶段：核心功能（1-2周）

1. ✅ 使用 `create_agent` 创建饮食训练 agent
2. ✅ 实现 `ToolRuntime[UserContext]` 上下文管理
3. ✅ 使用 `ToolStrategy(DailyPlan)` 结构化输出
4. ✅ 集成 `InMemorySaver` 记忆管理

### 第二阶段：用户体验（1-2周）

5. 实现流式输出到前端
6. 添加对话式计划调整
7. 优化工具调用逻辑

### 第三阶段：高级功能（2-3周）

8. 多模态输入支持（食物照片识别）
9. 服务器端工具集成（如果需要）
10. 推理过程可视化（如果模型支持）

## 🎯 预期效果

实施这些**真实的**官方推荐特性后，我们的饮食训练应用将获得：

### 用户体验提升
- ✅ **更快的响应** - 流式输出
- ✅ **更智能的对话** - 记忆和上下文
- ✅ **更准确的计划** - 结构化输出和工具调用
- ✅ **更个性化的服务** - 运行时上下文管理

### 技术优势
- ✅ **生产就绪** - 1.x 稳定 API
- ✅ **易于维护** - 简化的架构
- ✅ **高性能** - 优化的执行
- ✅ **可扩展** - 基于 LangGraph

### 业务价值
- ✅ **用户留存** - 更好的体验
- ✅ **个性化** - 智能推荐
- ✅ **专业性** - 科学的计算
- ✅ **可信度** - 透明的推理

## 📚 参考资源

- [LangChain 1.x 官方文档](https://docs.langchain.com/oss/python/langchain/overview)
- [Quickstart 指南](https://docs.langchain.com/oss/python/langchain/quickstart)
- [Agents 文档](https://docs.langchain.com/oss/python/langchain/agents)
- [Models 文档](https://docs.langchain.com/oss/python/langchain/models)
- [Tools 文档](https://docs.langchain.com/oss/python/langchain/tools)
- [LangGraph 文档](https://docs.langchain.com/oss/python/langgraph/overview)

---

**总结**: 基于真实的官方文档，LangChain 1.x 提供了强大而稳定的 API。通过采用官方推荐的模式（`create_agent`, `init_chat_model`, `@tool`, `ToolRuntime`, `ToolStrategy`, `InMemorySaver`），我们可以构建一个更智能、更可靠的饮食训练计划应用。
