# AI 智能体实现指南

## 技术栈版本

- **LangChain**: 1.1.0 (最新稳定版 - 1.x 系列) ✅ 已测试
- **LangChain-Core**: 1.1.0 ✅ 已测试
- **LangChain-Community**: 0.4.1 (注意：community 还在 0.4.x) ✅ 已测试
- **LangGraph**: 1.0.4 (最新稳定版 - 1.x 系列) ✅ 已测试
- **LangChain-OpenAI**: 1.1.0 ✅ 已测试
- **ChromaDB**: 0.5.23
- **OpenAI**: 1.58.1

**重要说明**: `langchain-community` 目前最新版本是 0.4.1，不是 1.x。这是正常的，因为 community 包的版本号独立管理。

## LangChain 1.x 和 LangGraph 1.x 的主要变化

### 1. LangChain 1.x 新特性

#### 核心改进
- **生产就绪**: 1.x 版本标志着 API 稳定，适合生产环境
- **完全的类型安全**: 完全支持 Pydantic v2.10+
- **统一的 Runnable 接口**: 所有组件都实现 `Runnable` 接口
- **改进的流式支持**: 原生支持 streaming 和 async
- **模块化架构**: 清晰分离为 `langchain-core`, `langchain-community`, `langchain-openai`
- **更好的错误处理**: 改进的异常和错误消息
- **性能优化**: 更快的执行速度和更低的内存占用

#### 新的 API 模式
```python
# 旧版本 (0.1.x)
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings

# 新版本 (1.x)
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
```

### 2. LangGraph 1.x 新特性

#### 生产就绪的状态图
```python
from langgraph.graph import StateGraph, END, START
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

# 1.x 版本的状态定义（更稳定）
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]  # 自动合并消息
    user_preferences: dict
    retrieved_context: dict
    generated_plan: dict
```

#### 改进的节点和边定义
```python
# 创建图
workflow = StateGraph(AgentState)

# 添加节点
workflow.add_node("understand", understand_intent)
workflow.add_node("retrieve", retrieve_context)
workflow.add_node("generate", generate_plan)

# 1.x 版本的边定义（更清晰）
workflow.add_edge(START, "understand")
workflow.add_edge("understand", "retrieve")
workflow.add_edge("retrieve", "generate")
workflow.add_edge("generate", END)

# 条件边（支持更复杂的路由逻辑）
workflow.add_conditional_edges(
    "understand",
    should_retrieve,  # 路由函数
    {
        "retrieve": "retrieve",
        "generate": "generate",
        "end": END
    }
)

# 编译图（1.x 支持更多编译选项）
app = workflow.compile(
    checkpointer=None,  # 可选：添加检查点以支持持久化
    interrupt_before=[],  # 可选：在特定节点前中断
    interrupt_after=[]   # 可选：在特定节点后中断
)
```

#### 新增功能：持久化和检查点
```python
from langgraph.checkpoint.sqlite import SqliteSaver

# 使用 SQLite 作为检查点存储
memory = SqliteSaver.from_conn_string(":memory:")

# 编译时添加检查点
app = workflow.compile(checkpointer=memory)

# 使用线程 ID 进行对话
config = {"configurable": {"thread_id": "user_123"}}
result = app.invoke(initial_state, config=config)
```

## 实现架构

### 1. RAG (检索增强生成) 流程

```python
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_community.vectorstores import Chroma
from langgraph.graph import StateGraph, END, START
from typing import TypedDict, Annotated, List
from langgraph.graph.message import add_messages

# 1. 初始化组件
llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0.7)
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# 2. 向量存储
vectorstore = Chroma(
    collection_name="diet_training",
    embedding_function=embeddings,
    persist_directory="./data/chroma"
)

# 3. 状态定义
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    user_preferences: dict
    historical_plans: list
    retrieved_context: dict
    generated_plan: dict
    current_step: str

# 4. 节点函数
def understand_intent(state: AgentState) -> AgentState:
    """理解用户意图"""
    messages = state["messages"]
    last_message = messages[-1].content
    
    # 使用 LLM 分析意图
    prompt = ChatPromptTemplate.from_messages([
        ("system", "分析用户的意图，判断是查询、生成计划还是其他操作。"),
        ("human", "{input}")
    ])
    
    chain = prompt | llm | StrOutputParser()
    intent = chain.invoke({"input": last_message})
    
    state["current_step"] = intent
    return state

def retrieve_context(state: AgentState) -> AgentState:
    """从向量数据库检索相关上下文"""
    messages = state["messages"]
    last_message = messages[-1].content
    
    # 语义搜索
    docs = vectorstore.similarity_search(last_message, k=5)
    
    state["retrieved_context"] = {
        "similar_plans": [doc.page_content for doc in docs],
        "metadata": [doc.metadata for doc in docs]
    }
    
    return state

def generate_plan(state: AgentState) -> AgentState:
    """生成饮食训练计划"""
    messages = state["messages"]
    context = state["retrieved_context"]
    preferences = state["user_preferences"]
    
    # 构建提示词
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个专业的饮食训练计划助手。
        
用户偏好：{preferences}
相似历史计划：{context}

请生成一个科学合理的饮食训练计划，输出JSON格式：
{{
    "meals": [
        {{"name": "早餐", "calories": 500, "items": ["燕麦", "牛奶"]}}
    ],
    "exercises": [
        {{"name": "跑步", "duration": 30, "calories": 300}}
    ],
    "reasoning": "计划制定的理由"
}}"""),
        ("human", "{input}")
    ])
    
    # 使用 JsonOutputParser
    parser = JsonOutputParser()
    chain = prompt | llm | parser
    
    result = chain.invoke({
        "input": messages[-1].content,
        "preferences": preferences,
        "context": context
    })
    
    state["generated_plan"] = result
    return state

# 5. 构建图
def create_agent():
    workflow = StateGraph(AgentState)
    
    # 添加节点
    workflow.add_node("understand", understand_intent)
    workflow.add_node("retrieve", retrieve_context)
    workflow.add_node("generate", generate_plan)
    
    # 添加边
    workflow.add_edge(START, "understand")
    workflow.add_edge("understand", "retrieve")
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", END)
    
    # 编译
    return workflow.compile()

# 6. 使用
agent = create_agent()

# 调用
result = agent.invoke({
    "messages": [HumanMessage(content="帮我生成明天的饮食训练计划")],
    "user_preferences": {"goal": "减脂", "allergies": []},
    "historical_plans": [],
    "retrieved_context": {},
    "generated_plan": {},
    "current_step": ""
})
```

### 2. 工具使用 (Tools)

```python
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_openai_tools_agent

@tool
def get_user_preferences(user_id: str) -> dict:
    """获取用户的饮食偏好和目标"""
    # 从数据库查询
    return {"goal": "减脂", "allergies": ["花生"]}

@tool
def search_similar_plans(query: str) -> list:
    """语义搜索相似的历史计划"""
    docs = vectorstore.similarity_search(query, k=3)
    return [doc.page_content for doc in docs]

@tool
def calculate_nutrition(meals: list) -> dict:
    """计算营养需求"""
    total_calories = sum(meal["calories"] for meal in meals)
    return {"total_calories": total_calories}

# 创建工具列表
tools = [get_user_preferences, search_similar_plans, calculate_nutrition]

# 创建带工具的智能体
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个饮食训练计划助手，可以使用工具来帮助用户。"),
    ("placeholder", "{chat_history}"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_openai_tools_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# 使用
result = agent_executor.invoke({
    "input": "帮我生成一个减脂计划",
    "chat_history": []
})
```

### 3. 向量数据库集成

```python
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

# 初始化
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = Chroma(
    collection_name="diet_training",
    embedding_function=embeddings,
    persist_directory="./data/chroma"
)

# 添加文档
def add_conversation_to_vector_db(conversation: dict):
    """将对话添加到向量数据库"""
    doc = Document(
        page_content=conversation["content"],
        metadata={
            "role": conversation["role"],
            "timestamp": conversation["timestamp"],
            "type": "conversation"
        }
    )
    vectorstore.add_documents([doc])

def add_plan_to_vector_db(plan: dict):
    """将计划添加到向量数据库"""
    content = f"日期: {plan['date']}\n"
    content += f"餐食: {', '.join([m['name'] for m in plan['meals']])}\n"
    content += f"运动: {', '.join([e['name'] for e in plan['exercises']])}"
    
    doc = Document(
        page_content=content,
        metadata={
            "date": plan["date"],
            "type": "plan",
            "total_calories": plan.get("total_calories", 0)
        }
    )
    vectorstore.add_documents([doc])

# 搜索
def search_similar_conversations(query: str, k: int = 5):
    """搜索相似对话"""
    results = vectorstore.similarity_search(
        query,
        k=k,
        filter={"type": "conversation"}
    )
    return results

def search_similar_plans(query: str, k: int = 5):
    """搜索相似计划"""
    results = vectorstore.similarity_search(
        query,
        k=k,
        filter={"type": "plan"}
    )
    return results
```

### 4. 流式输出

```python
from langchain_core.runnables import RunnablePassthrough

# 流式生成
async def stream_plan_generation(user_input: str):
    """流式生成计划"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个饮食训练计划助手。"),
        ("human", "{input}")
    ])
    
    chain = prompt | llm
    
    async for chunk in chain.astream({"input": user_input}):
        yield chunk.content

# 在 FastAPI 中使用
from fastapi.responses import StreamingResponse

@app.post("/api/ai/chat/stream")
async def chat_stream(message: str):
    return StreamingResponse(
        stream_plan_generation(message),
        media_type="text/event-stream"
    )
```

## 关键改进点

### 1. 使用最新的 Embeddings 模型
```python
# 使用 OpenAI 最新的 embedding 模型
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",  # 更快更便宜
    # model="text-embedding-3-large",  # 更高质量
)
```

### 2. 结构化输出
```python
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

class DietPlan(BaseModel):
    meals: list[dict] = Field(description="餐食列表")
    exercises: list[dict] = Field(description="运动列表")
    reasoning: str = Field(description="计划理由")

parser = JsonOutputParser(pydantic_object=DietPlan)
chain = prompt | llm | parser
```

### 3. 记忆管理
```python
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# 自定义消息历史
class SQLChatMessageHistory(BaseChatMessageHistory):
    def __init__(self, session_id: str, db: Session):
        self.session_id = session_id
        self.db = db
    
    def add_message(self, message):
        # 保存到数据库
        pass
    
    def get_messages(self):
        # 从数据库读取
        pass

# 使用
chain_with_history = RunnableWithMessageHistory(
    chain,
    lambda session_id: SQLChatMessageHistory(session_id, db),
    input_messages_key="input",
    history_messages_key="chat_history",
)
```

## 性能优化

### 1. 批量处理
```python
# 批量向量化
texts = ["文本1", "文本2", "文本3"]
embeddings_list = embeddings.embed_documents(texts)
```

### 2. 缓存
```python
from langchain.cache import SQLiteCache
from langchain.globals import set_llm_cache

set_llm_cache(SQLiteCache(database_path=".langchain.db"))
```

### 3. 异步调用
```python
# 异步调用 LLM
result = await llm.ainvoke("你的问题")

# 异步流式
async for chunk in llm.astream("你的问题"):
    print(chunk.content)
```

## 总结

使用最新版本的 LangChain 和 LangGraph，我们可以：

1. **更好的类型安全**: Pydantic v2 完全支持
2. **更强大的 RAG**: 改进的向量检索和上下文管理
3. **更灵活的工具使用**: 新的工具 API 更简洁
4. **更好的流式支持**: 原生支持流式输出
5. **更模块化**: 清晰的模块分离，易于维护

这些改进将使我们的 AI 智能体更加强大、可靠和易于扩展。
