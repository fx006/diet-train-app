# LangChain 1.x 和 LangGraph 1.x 完整指南

## 版本信息

- **LangChain**: 1.1.0
- **LangChain-Core**: 1.1.0  
- **LangChain-Community**: 1.1.0
- **LangGraph**: 1.0.4
- **LangChain-OpenAI**: 1.1.0

## 为什么选择 1.x 版本？

### 1. 生产就绪
- API 稳定，不会有破坏性变更
- 经过充分测试
- 大规模生产环境验证

### 2. 性能优化
- 更快的执行速度
- 更低的内存占用
- 优化的向量搜索

### 3. 更好的开发体验
- 完整的类型提示
- 清晰的错误消息
- 丰富的文档

## 核心概念

### 1. Runnable 接口

所有 LangChain 组件都实现 `Runnable` 接口：

```python
from langchain_core.runnables import Runnable

# 所有这些方法都可用
result = runnable.invoke(input)           # 同步调用
result = await runnable.ainvoke(input)    # 异步调用
for chunk in runnable.stream(input):      # 流式输出
    print(chunk)
async for chunk in runnable.astream(input):  # 异步流式
    print(chunk)
results = runnable.batch([input1, input2])   # 批量处理
```

### 2. LCEL (LangChain Expression Language)

使用管道操作符 `|` 链接组件：

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 创建链
chain = (
    ChatPromptTemplate.from_template("告诉我关于{topic}的信息")
    | ChatOpenAI(model="gpt-4")
    | StrOutputParser()
)

# 调用
result = chain.invoke({"topic": "饮食营养"})
```

## 完整实现示例

### 1. 基础 LLM 调用

```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# 初始化 LLM
llm = ChatOpenAI(
    model="gpt-4-turbo-preview",
    temperature=0.7,
    api_key="your-api-key"
)

# 方式 1: 直接调用
response = llm.invoke([
    SystemMessage(content="你是一个饮食营养专家"),
    HumanMessage(content="如何制定减脂计划？")
])
print(response.content)

# 方式 2: 使用提示词模板
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个{role}"),
    ("human", "{question}")
])

chain = prompt | llm
response = chain.invoke({
    "role": "饮食营养专家",
    "question": "如何制定减脂计划？"
})
```

### 2. 结构化输出

```python
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List

# 定义输出结构
class Meal(BaseModel):
    name: str = Field(description="餐食名称")
    calories: int = Field(description="热量")
    ingredients: List[str] = Field(description="食材列表")

class DailyPlan(BaseModel):
    date: str = Field(description="日期")
    meals: List[Meal] = Field(description="餐食列表")
    total_calories: int = Field(description="总热量")

# 创建解析器
parser = JsonOutputParser(pydantic_object=DailyPlan)

# 创建提示词
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个饮食计划助手。{format_instructions}"),
    ("human", "为我生成{date}的饮食计划")
])

# 创建链
chain = prompt | llm | parser

# 调用
result = chain.invoke({
    "date": "2024-01-15",
    "format_instructions": parser.get_format_instructions()
})

# result 是一个字典，符合 DailyPlan 结构
print(result["meals"][0]["name"])
```

### 3. 向量存储和 RAG

```python
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

# 初始化 embeddings
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",  # 最新模型
    api_key="your-api-key"
)

# 创建向量存储
vectorstore = Chroma(
    collection_name="diet_plans",
    embedding_function=embeddings,
    persist_directory="./chroma_db"
)

# 添加文档
docs = [
    Document(
        page_content="早餐：燕麦粥配水果，热量约300卡",
        metadata={"type": "meal", "time": "breakfast"}
    ),
    Document(
        page_content="午餐：鸡胸肉沙拉，热量约450卡",
        metadata={"type": "meal", "time": "lunch"}
    )
]
vectorstore.add_documents(docs)

# 搜索
results = vectorstore.similarity_search(
    "低热量早餐",
    k=3,
    filter={"time": "breakfast"}
)

for doc in results:
    print(doc.page_content)
    print(doc.metadata)
```

### 4. RAG 链

```python
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# 创建检索器
retriever = vectorstore.as_retriever(
    search_kwargs={"k": 3}
)

# 创建 RAG 链
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

rag_chain = (
    {
        "context": retriever | format_docs,
        "question": RunnablePassthrough()
    }
    | ChatPromptTemplate.from_template("""
根据以下上下文回答问题：

上下文：
{context}

问题：{question}

回答：""")
    | llm
    | StrOutputParser()
)

# 使用
answer = rag_chain.invoke("推荐一个低热量早餐")
print(answer)
```

### 5. LangGraph 状态图

```python
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

# 定义状态
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    user_goal: str
    plan: dict
    step: str

# 定义节点函数
def understand_goal(state: AgentState) -> AgentState:
    """理解用户目标"""
    messages = state["messages"]
    last_message = messages[-1].content
    
    # 使用 LLM 分析
    prompt = ChatPromptTemplate.from_template(
        "分析用户目标：{input}\n返回目标类型（减脂/增肌/维持）"
    )
    chain = prompt | llm | StrOutputParser()
    goal = chain.invoke({"input": last_message})
    
    state["user_goal"] = goal
    state["step"] = "goal_understood"
    return state

def retrieve_knowledge(state: AgentState) -> AgentState:
    """检索相关知识"""
    goal = state["user_goal"]
    
    # 从向量数据库检索
    docs = vectorstore.similarity_search(goal, k=5)
    
    state["step"] = "knowledge_retrieved"
    return state

def generate_plan(state: AgentState) -> AgentState:
    """生成计划"""
    goal = state["user_goal"]
    
    prompt = ChatPromptTemplate.from_template(
        "为{goal}目标生成饮食训练计划"
    )
    parser = JsonOutputParser(pydantic_object=DailyPlan)
    chain = prompt | llm | parser
    
    plan = chain.invoke({"goal": goal})
    state["plan"] = plan
    state["step"] = "plan_generated"
    return state

# 创建图
workflow = StateGraph(AgentState)

# 添加节点
workflow.add_node("understand", understand_goal)
workflow.add_node("retrieve", retrieve_knowledge)
workflow.add_node("generate", generate_plan)

# 添加边
workflow.add_edge(START, "understand")
workflow.add_edge("understand", "retrieve")
workflow.add_edge("retrieve", "generate")
workflow.add_edge("generate", END)

# 编译
app = workflow.compile()

# 使用
from langchain_core.messages import HumanMessage

result = app.invoke({
    "messages": [HumanMessage(content="我想减脂")],
    "user_goal": "",
    "plan": {},
    "step": "start"
})

print(result["plan"])
```

### 6. 带持久化的 LangGraph

```python
from langgraph.checkpoint.sqlite import SqliteSaver

# 创建持久化存储
memory = SqliteSaver.from_conn_string("checkpoints.db")

# 编译时添加检查点
app = workflow.compile(checkpointer=memory)

# 使用线程 ID 进行对话
config = {"configurable": {"thread_id": "user_123"}}

# 第一次调用
result1 = app.invoke({
    "messages": [HumanMessage(content="我想减脂")],
    "user_goal": "",
    "plan": {},
    "step": "start"
}, config=config)

# 第二次调用（会记住之前的状态）
result2 = app.invoke({
    "messages": [HumanMessage(content="调整一下计划")],
    "user_goal": result1["user_goal"],
    "plan": result1["plan"],
    "step": result1["step"]
}, config=config)
```

### 7. 流式输出

```python
# 同步流式
for chunk in chain.stream({"topic": "营养"}):
    print(chunk, end="", flush=True)

# 异步流式
async def stream_response():
    async for chunk in chain.astream({"topic": "营养"}):
        print(chunk, end="", flush=True)

# 在 FastAPI 中使用
from fastapi.responses import StreamingResponse

@app.post("/chat/stream")
async def chat_stream(message: str):
    async def generate():
        async for chunk in chain.astream({"input": message}):
            yield chunk
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )
```

### 8. 工具使用

```python
from langchain_core.tools import tool
from langchain.agents import create_openai_tools_agent, AgentExecutor

@tool
def search_meals(query: str) -> list:
    """搜索餐食信息"""
    results = vectorstore.similarity_search(query, k=3)
    return [doc.page_content for doc in results]

@tool
def calculate_calories(meals: list) -> int:
    """计算总热量"""
    # 实现计算逻辑
    return sum(meal.get("calories", 0) for meal in meals)

# 创建工具列表
tools = [search_meals, calculate_calories]

# 创建智能体
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个饮食助手，可以使用工具帮助用户。"),
    ("placeholder", "{chat_history}"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_openai_tools_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# 使用
result = agent_executor.invoke({
    "input": "帮我找一些低热量的早餐选项",
    "chat_history": []
})
```

## 最佳实践

### 1. 错误处理

```python
from langchain_core.runnables import RunnableConfig

try:
    result = chain.invoke(
        {"input": "问题"},
        config=RunnableConfig(
            max_concurrency=5,
            recursion_limit=10
        )
    )
except Exception as e:
    print(f"错误: {e}")
```

### 2. 缓存

```python
from langchain.cache import SQLiteCache
from langchain.globals import set_llm_cache

# 设置缓存
set_llm_cache(SQLiteCache(database_path=".langchain.db"))

# 第一次调用会访问 API
result1 = llm.invoke("什么是健康饮食？")

# 第二次调用会使用缓存
result2 = llm.invoke("什么是健康饮食？")  # 更快！
```

### 3. 批量处理

```python
# 批量调用
inputs = [
    {"topic": "早餐"},
    {"topic": "午餐"},
    {"topic": "晚餐"}
]

results = chain.batch(inputs)
```

### 4. 异步处理

```python
import asyncio

async def process_multiple():
    tasks = [
        chain.ainvoke({"topic": "早餐"}),
        chain.ainvoke({"topic": "午餐"}),
        chain.ainvoke({"topic": "晚餐"})
    ]
    results = await asyncio.gather(*tasks)
    return results

# 运行
results = asyncio.run(process_multiple())
```

## 性能优化

### 1. 使用更快的 Embedding 模型

```python
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",  # 更快更便宜
    # model="text-embedding-3-large",  # 更高质量但更慢
)
```

### 2. 限制上下文长度

```python
retriever = vectorstore.as_retriever(
    search_kwargs={
        "k": 3,  # 只检索 3 个文档
        "fetch_k": 10  # 先获取 10 个，然后重排序选 3 个
    }
)
```

### 3. 使用流式输出

```python
# 用户可以更快看到响应
for chunk in chain.stream(input):
    print(chunk, end="", flush=True)
```

## 总结

LangChain 1.x 和 LangGraph 1.x 提供了：

✅ **稳定的 API** - 生产就绪
✅ **更好的性能** - 优化的执行速度
✅ **完整的类型安全** - Pydantic v2 支持
✅ **丰富的功能** - RAG、工具、持久化
✅ **优秀的开发体验** - 清晰的文档和错误消息

这些版本是构建生产级 AI 应用的最佳选择！
