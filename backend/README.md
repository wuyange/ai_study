# AI 聊天后端 API

基于 FastAPI 和 AutoGen 构建的 AI 聊天后端服务，支持 SSE 流式输出。

## 技术栈

- FastAPI - 现代 Python Web 框架
- AutoGen - 微软开源的 AI 代理框架
- SSE (Server-Sent Events) - 服务器推送事件
- Uvicorn - ASGI 服务器

## 功能特性

- 🚀 基于 AutoGen 的智能对话
- 📡 SSE 流式输出
- 🔐 CORS 跨域支持
- ⚡ 异步处理
- 🎯 RESTful API 设计

## 安装

### 1. 创建虚拟环境（可选）

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 安装 AutoGen

```bash
pip install autogen-agentchat autogen-ext[openai]
```

### 4. 配置环境变量

复制 `.env.example` 到 `.env` 并填入您的配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
OPENAI_API_KEY=your_actual_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1
MODEL_NAME=gpt-4o
```

## 运行

### 开发模式

```bash
python main.py
```

或使用 uvicorn：

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 生产模式

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API 文档

启动服务后，访问：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 端点

### 1. 健康检查

```http
GET /api/health
```

### 2. 非流式聊天

```http
POST /api/chat
Content-Type: application/json

{
  "message": "你好，你是谁？"
}
```

### 3. 流式聊天（SSE）

```http
POST /api/chat/stream
Content-Type: application/json

{
  "message": "给我讲个故事"
}
```

响应格式：

```
data: {"content": "文本块1", "role": "assistant"}

data: {"content": "文本块2", "role": "assistant"}

data: [DONE]
```

## 测试

### 测试聊天服务

```bash
python chat_service.py
```

### 使用 curl 测试 API

```bash
# 非流式
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "你好"}'

# 流式
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "你好"}' \
  --no-buffer
```

## 项目结构

```
backend/
├── main.py                 # FastAPI 主应用
├── chat_service.py         # AutoGen 聊天服务
├── requirements.txt        # Python 依赖
├── .env.example           # 环境变量示例
├── .env                   # 环境变量配置（需创建）
├── .gitignore            # Git 忽略文件
└── README.md             # 项目文档
```

## 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| OPENAI_API_KEY | OpenAI API 密钥 | 必填 |
| OPENAI_API_BASE | API 基础 URL | https://api.openai.com/v1 |
| MODEL_NAME | 模型名称 | gpt-4o |
| HOST | 服务器地址 | 0.0.0.0 |
| PORT | 服务器端口 | 8000 |
| CORS_ORIGINS | 允许的跨域源 | http://localhost:3000 |

## 故障排除

### 1. ImportError: No module named 'autogen_agentchat'

确保已安装 AutoGen：

```bash
pip install autogen-agentchat autogen-ext[openai]
```

### 2. OPENAI_API_KEY 未设置

检查 `.env` 文件是否存在且配置正确。

### 3. CORS 错误

在 `.env` 中添加前端 URL 到 `CORS_ORIGINS`：

```env
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

## 许可证

MIT

