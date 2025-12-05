# 饮食训练计划追踪应用 - 后端文档

## 📚 文档索引

### 核心文档

1. **[REAL_LANGCHAIN_1X_FEATURES.md](./REAL_LANGCHAIN_1X_FEATURES.md)** 🎯 **基于真实官方文档** ⭐ 最新
   - 基于 LangChain 官方文档的真实特性分析
   - 真实的 API 和最佳实践（非假设）
   - 针对饮食训练项目的具体应用建议
   - 完整的代码示例和实施计划

2. **[COMPATIBILITY_REPORT.md](./COMPATIBILITY_REPORT.md)** 🔥 必读
   - LangChain 1.x 兼容性测试报告
   - 实际测试结果和验证
   - 版本说明和注意事项

3. **[LANGCHAIN_1X_GUIDE.md](./LANGCHAIN_1X_GUIDE.md)** ⭐ 推荐阅读
   - LangChain 1.x 和 LangGraph 1.x 完整指南
   - 详细的代码示例
   - 最佳实践和性能优化

4. **[AI_AGENT_IMPLEMENTATION.md](./AI_AGENT_IMPLEMENTATION.md)**
   - AI 智能体实现指南
   - LangChain 和 LangGraph 架构说明
   - RAG 流程详解

5. **[VERSION_UPDATE.md](./VERSION_UPDATE.md)**
   - 依赖版本更新说明
   - 迁移指南
   - 破坏性变更说明

## 🎯 技术栈版本

### AI 框架（生产就绪的 1.x 版本）

| 包名 | 版本 | 说明 |
|------|------|------|
| **langchain** | **1.1.0** | 🎉 主框架，1.x 稳定版 ✅ 已测试 |
| **langchain-core** | **1.1.0** | 核心组件 ✅ 已测试 |
| **langchain-community** | **0.4.1** | 社区集成 ⚠️ 注意版本号 ✅ 已测试 |
| **langgraph** | **1.0.4** | 🎉 状态图框架，1.x 稳定版 ✅ 已测试 |
| **langchain-openai** | **1.1.0** | OpenAI 集成 ✅ 已测试 |

**重要**: `langchain-community` 最新版本是 0.4.1（不是 1.x），这是正常的版本管理策略，与 langchain 1.1.0 完全兼容。
| **chromadb** | **0.5.23** | 向量数据库 |
| **openai** | **1.58.1** | OpenAI API |

### Web 框架

| 包名 | 版本 |
|------|------|
| fastapi | 0.115.6 |
| uvicorn | 0.34.0 |
| pydantic | 2.10.3 |

### 数据库

| 包名 | 版本 |
|------|------|
| sqlalchemy | 2.0.36 |
| alembic | 1.14.0 |

### 测试

| 包名 | 版本 |
|------|------|
| pytest | 8.3.4 |
| hypothesis | 6.122.3 |

## 🚀 快速开始

### 1. 安装依赖

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，设置 OPENAI_API_KEY 等
```

### 3. 初始化数据库

```bash
mkdir -p data
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

### 4. 运行测试

```bash
pytest tests/ -v
```

### 5. 启动服务

```bash
uvicorn app.main:app --reload
```

## 📖 核心概念

### LangChain 1.x

LangChain 1.x 是**生产就绪**的版本，提供：

- ✅ **稳定的 API** - 不会有破坏性变更
- ✅ **完整的类型安全** - Pydantic v2 支持
- ✅ **统一的 Runnable 接口** - 所有组件都可以 invoke/stream/batch
- ✅ **模块化架构** - 清晰的包分离

#### 基础示例

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

### LangGraph 1.x

LangGraph 1.x 是**生产就绪**的状态图框架，提供：

- ✅ **稳定的 API** - 1.x 版本保证向后兼容
- ✅ **持久化支持** - 内置检查点机制
- ✅ **条件路由** - 复杂的工作流控制
- ✅ **流式输出** - 实时响应

#### 基础示例

```python
from langgraph.graph import StateGraph, START, END
from typing import TypedDict

class State(TypedDict):
    messages: list
    result: str

def process(state: State) -> State:
    # 处理逻辑
    return state

# 创建图
workflow = StateGraph(State)
workflow.add_node("process", process)
workflow.add_edge(START, "process")
workflow.add_edge("process", END)

# 编译并使用
app = workflow.compile()
result = app.invoke({"messages": [], "result": ""})
```

### RAG (检索增强生成)

使用向量数据库增强 LLM 的上下文：

```python
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

# 初始化
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = Chroma(
    collection_name="diet_plans",
    embedding_function=embeddings,
    persist_directory="./chroma_db"
)

# 搜索
results = vectorstore.similarity_search("低热量早餐", k=3)
```

## 🏗️ 项目结构

```
backend/
├── app/
│   ├── models/              # SQLAlchemy 模型
│   │   ├── plan.py
│   │   ├── user_preference.py
│   │   └── ai_conversation.py
│   ├── repositories/        # 数据访问层
│   │   ├── plan_repository.py
│   │   ├── preference_repository.py
│   │   └── conversation_repository.py
│   ├── services/            # 业务逻辑层
│   │   └── ai_agent.py     # AI 智能体服务
│   ├── routers/             # API 路由
│   ├── config.py            # 配置管理
│   ├── database.py          # 数据库连接
│   └── main.py              # 应用入口
├── tests/                   # 测试
│   ├── test_plan_repository.py
│   ├── test_preference_repository.py
│   └── test_conversation_repository.py
├── docs/                    # 文档
│   ├── AI_AGENT_IMPLEMENTATION.md
│   ├── LANGCHAIN_1X_GUIDE.md
│   └── VERSION_UPDATE.md
├── alembic/                 # 数据库迁移
├── requirements.txt         # 依赖
└── .env.example            # 环境变量示例
```

## 🧪 测试

### 运行兼容性测试

首先验证 LangChain 1.x 兼容性：

```bash
python test_langchain_1x.py
```

预期输出：
```
🎉 所有测试通过！LangChain 1.x 和 LangGraph 1.x 完全兼容！
```

### 运行所有测试

```bash
pytest tests/ -v
```

### 运行特定测试

```bash
pytest tests/test_plan_repository.py -v
```

### 查看测试覆盖率

```bash
pytest tests/ --cov=app --cov-report=html
```

### 属性测试

项目使用 Hypothesis 进行属性测试，验证：

- ✅ 数据持久化往返一致性
- ✅ 用户偏好持久性
- ✅ AI 消息持久化

每个测试运行 100+ 个随机生成的测试用例！

## 📝 开发指南

### 添加新的 API 端点

1. 在 `app/routers/` 创建路由文件
2. 定义 Pydantic 模型
3. 实现业务逻辑
4. 在 `app/main.py` 注册路由

### 添加新的数据模型

1. 在 `app/models/` 创建模型文件
2. 在 `app/repositories/` 创建仓储类
3. 创建 Alembic 迁移
4. 编写测试

### 使用 AI 功能

参考 `app/services/ai_agent.py` 和 `docs/LANGCHAIN_1X_GUIDE.md`

## 🔧 配置

### 环境变量

在 `.env` 文件中配置：

```env
# 数据库
DATABASE_URL=sqlite:///./data/app.db

# OpenAI
OPENAI_API_KEY=your_api_key_here

# ChromaDB
CHROMA_PERSIST_DIRECTORY=./data/chroma

# 应用
APP_NAME=Diet Training Tracker
DEBUG=false
```

### 数据库切换

#### 使用 SQLite（默认）

```env
DATABASE_URL=sqlite:///./data/app.db
```

#### 使用 MySQL

```env
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/diet_tracker
```

## 🎓 学习资源

### 官方文档

- [LangChain 文档](https://python.langchain.com/)
- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org/)

### 项目文档

- [兼容性测试报告](./COMPATIBILITY_REPORT.md) 🔥
- [LangChain 1.x 新特性应用](./LANGCHAIN_1X_NEW_FEATURES.md) 🎯 新增
- [LangChain 1.x 完整指南](./LANGCHAIN_1X_GUIDE.md) ⭐
- [AI 智能体实现指南](./AI_AGENT_IMPLEMENTATION.md)
- [版本更新说明](./VERSION_UPDATE.md)

## 🤝 贡献

欢迎贡献！请确保：

1. 所有测试通过
2. 代码符合 PEP 8 规范
3. 添加必要的文档
4. 使用类型提示

## 📄 许可证

MIT

---

**注意**: 本项目使用 LangChain 1.x 和 LangGraph 1.x，这些是**生产就绪**的稳定版本！
