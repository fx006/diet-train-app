# 饮食训练追踪器 🏋️‍♀️🥗

一个功能完整的全栈应用，用于追踪和管理每日饮食和运动计划，集成AI智能助手提供个性化建议。

## ✨ 核心功能

- 📅 **每日计划管理** - 记录和追踪每日的饮食和运动
- 📊 **数据统计** - 实时计算热量摄入、消耗和净值
- 📤 **文件导入** - 支持Excel和PDF文件快速导入数据
- ⏱️ **运动计时** - 正计时和倒计时功能
- 🤖 **AI智能助手** - 基于LangChain 1.x的对话式计划生成（支持RAG检索）
- 📈 **历史记录** - 查看训练历史和统计趋势
- 💾 **数据导出** - 导出为Excel或CSV格式
- ⚙️ **个性化设置** - 配置健身目标和饮食偏好

## 🎯 项目状态

- ✅ 后端功能 100% 完成（395个测试通过）
- ✅ 前端功能 95% 完成
- ✅ AI智能体集成完成（LangChain 1.x + RAG）
- ✅ 向量数据库集成完成（ChromaDB）

详细状态请查看 [PROJECT_STATUS.md](PROJECT_STATUS.md)

## 技术栈

### 后端
- Python 3.11+
- FastAPI (Web框架)
- SQLAlchemy (ORM)
- SQLite/MySQL (数据库)
- Alembic (数据库迁移)
- LangGraph (AI智能体框架)
- ChromaDB (向量数据库)

### 前端
- React 18 + TypeScript
- Vite (构建工具)
- Tailwind CSS (样式)
- Zustand (状态管理)
- React Query (数据获取)
- React Router (路由)

## 项目结构

```
.
├── backend/                 # 后端代码
│   ├── app/
│   │   ├── models/         # 数据模型
│   │   ├── routers/        # API路由
│   │   ├── config.py       # 配置管理
│   │   ├── database.py     # 数据库连接
│   │   └── main.py         # 应用入口
│   ├── alembic/            # 数据库迁移
│   ├── requirements.txt    # Python依赖
│   └── .env.example        # 环境变量示例
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── api/           # API客户端
│   │   ├── pages/         # 页面组件
│   │   ├── store/         # 状态管理
│   │   ├── types/         # TypeScript类型
│   │   ├── App.tsx        # 应用根组件
│   │   └── main.tsx       # 应用入口
│   ├── package.json       # Node依赖
│   └── vite.config.ts     # Vite配置
└── README.md              # 项目文档
```

## 快速开始

### 快速启动

#### 后端设置

1. 创建虚拟环境并安装依赖：
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. 配置环境变量：
```bash
cp .env.example .env
# 编辑 .env 文件，设置AI服务提供商
```

**重要**：需要配置AI服务提供商才能使用AI功能。详细配置指南请查看 [AI配置指南](./AI_CONFIGURATION.md)

3. 初始化数据库：
```bash
# 创建数据目录
mkdir -p data

# 运行数据库迁移
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

4. 启动开发服务器：
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端API将在 http://localhost:8000 运行

### 前端设置

1. 安装依赖：
```bash
cd frontend
npm install
```

2. 启动开发服务器：
```bash
npm run dev
```

前端应用将在 http://localhost:5173 运行

## 开发指南

### 数据库迁移

创建新的迁移：
```bash
cd backend
alembic revision --autogenerate -m "描述变更"
```

应用迁移：
```bash
alembic upgrade head
```

回滚迁移：
```bash
alembic downgrade -1
```

### API文档

启动后端服务后，访问以下地址查看API文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 环境变量

### 后端环境变量

在 `backend/.env` 文件中配置：

```env
# 数据库配置
DATABASE_URL=sqlite:///./data/app.db

# AI服务配置（支持多种提供商）
OPENAI_API_KEY=your_api_key
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL_NAME=gpt-3.5-turbo

# ChromaDB配置
CHROMA_PERSIST_DIRECTORY=./data/chroma

# 应用设置
APP_NAME=Diet Training Tracker
DEBUG=false
```

**AI服务提供商**：
- ✅ OpenAI 官方
- ✅ 硅基流动（SiliconFlow）
- ✅ DeepSeek
- ✅ 阿里云百炼
- ✅ 任何兼容OpenAI API的服务

详细配置说明请查看 [AI配置指南](./AI_CONFIGURATION.md)

### 使用MySQL

如果要使用MySQL而不是SQLite：

1. 创建数据库：
```sql
CREATE DATABASE diet_tracker CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'diet_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON diet_tracker.* TO 'diet_user'@'localhost';
FLUSH PRIVILEGES;
```

2. 更新 `.env` 文件：
```env
DATABASE_URL=mysql+pymysql://diet_user:your_password@localhost:3306/diet_tracker
```

## 部署

部署相关配置和文档将在后续版本中提供。

## 📚 文档

- [本地启动步骤](./本地启动步骤.md) - 快速启动指南
- [本地开发指南](./本地开发指南.md) - 详细的开发流程
- [AI配置指南](./AI_CONFIGURATION.md) - AI服务提供商配置
- [项目状态](./PROJECT_STATUS.md) - 当前开发进度

## 许可证

MIT
