# 依赖版本更新说明

## 更新概述

已将所有依赖更新到最新稳定版本，特别是 LangChain 和 LangGraph 生态系统。

## 主要版本变更

### AI 框架 (重大更新)

| 包名 | 旧版本 | 新版本 | 变更说明 |
|------|--------|--------|----------|
| langchain | 0.1.20 | **1.1.0** | 🎉 重大版本升级到 1.x，生产就绪！ |
| langchain-core | - | **1.1.0** | 新增核心包，1.x 稳定版 |
| langchain-community | - | **1.1.0** | 新增社区集成包，1.x 稳定版 |
| langgraph | 0.0.40 | **1.0.4** | 🎉 重大版本升级到 1.x，API 稳定！ |
| langchain-openai | 0.1.0 | **1.1.0** | 独立包，1.x 稳定版 |
| chromadb | 0.4.22 | **0.5.23** | 性能改进 |
| openai | 1.12.0 | **1.58.1** | 最新 API 支持 |

### Web 框架

| 包名 | 旧版本 | 新版本 |
|------|--------|--------|
| fastapi | 0.104.1 | **0.109.0** |
| uvicorn | 0.24.0 | **0.27.0** |
| pydantic | 2.5.0 | **2.5.3** |

### 数据库

| 包名 | 旧版本 | 新版本 |
|------|--------|--------|
| sqlalchemy | 2.0.23 | **2.0.25** |
| alembic | 1.12.1 | **1.13.1** |

### 测试

| 包名 | 旧版本 | 新版本 |
|------|--------|--------|
| pytest | 7.4.3 | **8.0.0** |
| hypothesis | 6.92.1 | **6.98.3** |

## LangChain 1.x 主要变更（生产就绪！）

### 1. 模块化架构（1.x 稳定版）

```python
# 旧版本 (0.1.x)
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings

# 新版本 (1.x) - 更清晰的模块分离，API 稳定
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import Chroma
```

**重要**: 1.x 版本标志着 API 稳定，不会有破坏性变更！

### 2. 改进的类型安全

- 完全支持 Pydantic v2
- 更好的类型提示
- 运行时类型检查

### 3. 统一的 Runnable 接口

所有组件都实现 `Runnable` 接口：
- `invoke()` - 同步调用
- `ainvoke()` - 异步调用
- `stream()` - 流式输出
- `astream()` - 异步流式输出
- `batch()` - 批量处理

### 4. 改进的输出解析

```python
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel

class MyOutput(BaseModel):
    field1: str
    field2: int

parser = JsonOutputParser(pydantic_object=MyOutput)
chain = prompt | llm | parser
```

## LangGraph 1.x 主要变更（生产就绪！）

### 1. 稳定的 API（1.x 版本）

- 从 0.0.x 到 **1.0.x**，API 完全稳定
- **生产环境就绪**，大规模应用验证
- 向后兼容保证

### 2. 改进的状态管理

```python
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]  # 自动合并消息
    data: dict
```

### 3. 新的图构建 API

```python
from langgraph.graph import StateGraph, START, END

workflow = StateGraph(State)
workflow.add_node("node1", func1)
workflow.add_edge(START, "node1")
workflow.add_edge("node1", END)
app = workflow.compile()
```

### 4. 条件边支持

```python
def should_continue(state):
    return "continue" if state["count"] < 10 else "end"

workflow.add_conditional_edges(
    "node1",
    should_continue,
    {
        "continue": "node2",
        "end": END
    }
)
```

## ChromaDB 0.5.x 主要变更

### 1. 性能改进

- 更快的向量搜索
- 优化的内存使用
- 改进的持久化

### 2. 新的 API

```python
from langchain_community.vectorstores import Chroma

vectorstore = Chroma(
    collection_name="my_collection",
    embedding_function=embeddings,
    persist_directory="./chroma_db"
)

# 添加文档
vectorstore.add_documents(documents)

# 搜索
results = vectorstore.similarity_search(query, k=5)

# 带过滤的搜索
results = vectorstore.similarity_search(
    query,
    k=5,
    filter={"type": "plan"}
)
```

## OpenAI 1.58.x 主要变更

### 1. 新的 Embeddings 模型

```python
from langchain_openai import OpenAIEmbeddings

# 推荐使用新模型
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small"  # 更快更便宜
    # model="text-embedding-3-large"  # 更高质量
)
```

### 2. 改进的 Chat 模型

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-4-turbo-preview",  # 最新模型
    temperature=0.7,
    streaming=True  # 支持流式输出
)
```

## 迁移指南

### 步骤 1: 更新依赖

```bash
cd backend
pip install -r requirements.txt
```

### 步骤 2: 更新导入语句

将所有旧的导入替换为新的模块化导入：

```python
# 替换这些
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma

# 为这些
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
```

### 步骤 3: 更新 LangGraph 代码

```python
# 旧版本
from langgraph.graph import StateGraph, END

# 新版本
from langgraph.graph import StateGraph, START, END

# 使用 START 而不是 set_entry_point
workflow.add_edge(START, "first_node")
```

### 步骤 4: 测试

运行所有测试确保兼容性：

```bash
pytest tests/ -v
```

## 新功能示例

### 1. 流式输出

```python
async def stream_response(query: str):
    chain = prompt | llm
    async for chunk in chain.astream({"input": query}):
        yield chunk.content
```

### 2. 结构化输出

```python
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel

class Plan(BaseModel):
    meals: list
    exercises: list

parser = JsonOutputParser(pydantic_object=Plan)
chain = prompt | llm | parser
result = chain.invoke({"input": "生成计划"})
```

### 3. 工具使用

```python
from langchain_core.tools import tool

@tool
def search_plans(query: str) -> list:
    """搜索历史计划"""
    return vectorstore.similarity_search(query)

tools = [search_plans]
agent = create_openai_tools_agent(llm, tools, prompt)
```

## 性能优化建议

### 1. 使用缓存

```python
from langchain.cache import SQLiteCache
from langchain.globals import set_llm_cache

set_llm_cache(SQLiteCache(database_path=".langchain.db"))
```

### 2. 批量处理

```python
# 批量向量化
texts = ["text1", "text2", "text3"]
embeddings_list = embeddings.embed_documents(texts)
```

### 3. 异步调用

```python
# 使用异步提高性能
result = await llm.ainvoke("query")
```

## 注意事项

1. **破坏性变更**: LangChain 0.3.x 有一些破坏性变更，需要更新代码
2. **测试**: 更新后务必运行完整的测试套件
3. **文档**: 参考最新的官方文档
4. **性能**: 新版本性能更好，但需要调整配置

## 参考资源

- [LangChain 0.3 迁移指南](https://python.langchain.com/docs/versions/migrating_chains/)
- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
- [ChromaDB 文档](https://docs.trychroma.com/)
- [OpenAI API 文档](https://platform.openai.com/docs/)

## 总结

这次更新带来了：
- ✅ 更稳定的 API
- ✅ 更好的性能
- ✅ 更强的类型安全
- ✅ 更丰富的功能
- ✅ 更好的开发体验

建议尽快迁移到新版本以获得这些改进。
