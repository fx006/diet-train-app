#!/bin/bash

# 本地开发环境启动脚本
# Docker启动中间件，代码本地运行

set -e

echo "🚀 饮食训练追踪器 - 本地开发环境"
echo "===================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查是否在项目根目录
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo -e "${RED}❌ 错误：请在项目根目录运行此脚本${NC}"
    exit 1
fi

# 步骤1: 检查Docker
echo -e "${YELLOW}📦 步骤1: 检查Docker...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker未运行，请先启动Docker Desktop${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker正在运行${NC}"
echo ""

# 步骤2: 配置环境变量
echo -e "${YELLOW}⚙️  步骤2: 检查环境变量...${NC}"
if [ ! -f "backend/.env" ]; then
    echo -e "${YELLOW}📝 创建backend/.env文件...${NC}"
    cp backend/.env.example backend/.env
    echo -e "${GREEN}✅ 已创建backend/.env${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  重要：请编辑backend/.env文件，配置以下内容：${NC}"
    echo "   1. 选择数据库（SQLite或MySQL）"
    echo "   2. 设置AI服务提供商和API Key"
    echo "   3. 配置模型名称"
    echo ""
    echo "支持的AI提供商："
    echo "  - OpenAI官方"
    echo "  - 硅基流动（API中转）"
    echo "  - DeepSeek"
    echo "  - 阿里云百炼"
    echo "  - 其他兼容OpenAI API的服务"
    echo ""
    read -p "按回车键继续编辑配置文件..." 
    ${EDITOR:-nano} backend/.env
fi

if [ ! -f "frontend/.env" ]; then
    cp frontend/.env.example frontend/.env
    echo -e "${GREEN}✅ 已创建frontend/.env${NC}"
fi
echo ""

# 步骤3: 选择数据库
echo -e "${YELLOW}🗄️  步骤3: 选择数据库${NC}"
echo "1) SQLite（简单，无需Docker）"
echo "2) MySQL（推荐，使用Docker）"
echo ""
read -p "请选择 (1 或 2，默认1): " db_choice
db_choice=${db_choice:-1}

if [ "$db_choice" = "2" ]; then
    echo ""
    echo -e "${YELLOW}🐳 启动MySQL Docker容器...${NC}"
    docker-compose -f docker-compose.dev.yml up -d mysql
    
    echo -e "${YELLOW}⏳ 等待MySQL启动...${NC}"
    sleep 10
    
    # 检查MySQL是否就绪
    until docker exec diet-tracker-mysql-dev mysqladmin ping -h localhost -u root -prootpassword --silent; do
        echo "等待MySQL就绪..."
        sleep 2
    done
    
    echo -e "${GREEN}✅ MySQL已启动${NC}"
    echo ""
    echo -e "${YELLOW}📝 请确保backend/.env中的DATABASE_URL设置为：${NC}"
    echo "   DATABASE_URL=mysql+pymysql://diet_user:userpassword@localhost:3306/diet_tracker"
    echo ""
    read -p "按回车键继续..."
else
    echo -e "${GREEN}✅ 使用SQLite数据库${NC}"
fi
echo ""

# 步骤4: 准备后端
echo -e "${YELLOW}🐍 步骤4: 准备后端环境...${NC}"
cd backend

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "创建Python虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "安装Python依赖..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# 创建数据目录
mkdir -p data data/chroma

# 运行数据库迁移
echo "运行数据库迁移..."
alembic upgrade head

echo -e "${GREEN}✅ 后端环境准备完成${NC}"
cd ..
echo ""

# 步骤5: 准备前端
echo -e "${YELLOW}📗 步骤5: 准备前端环境...${NC}"
cd frontend

if [ ! -d "node_modules" ]; then
    echo "安装Node.js依赖..."
    npm install
else
    echo "Node.js依赖已安装"
fi

echo -e "${GREEN}✅ 前端环境准备完成${NC}"
cd ..
echo ""

# 步骤6: 启动说明
echo -e "${GREEN}🎉 环境准备完成！${NC}"
echo ""
echo "======================================"
echo "现在需要打开两个终端窗口："
echo "======================================"
echo ""
echo -e "${YELLOW}终端1 - 启动后端：${NC}"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo -e "${YELLOW}终端2 - 启动前端：${NC}"
echo "  cd frontend"
echo "  npm run dev"
echo ""
echo "======================================"
echo "访问地址："
echo "======================================"
echo "  前端: http://localhost:5173"
echo "  后端API: http://localhost:8000"
echo "  API文档: http://localhost:8000/docs"
echo ""
echo "======================================"
echo "停止服务："
echo "======================================"
if [ "$db_choice" = "2" ]; then
    echo "  停止MySQL: docker-compose -f docker-compose.dev.yml down"
fi
echo "  停止后端: Ctrl+C"
echo "  停止前端: Ctrl+C"
echo ""

# 询问是否自动启动后端
read -p "是否在当前终端启动后端？(y/n，默认n): " start_backend
if [ "$start_backend" = "y" ]; then
    echo ""
    echo -e "${GREEN}🚀 启动后端服务...${NC}"
    echo ""
    cd backend
    source venv/bin/activate
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
fi
