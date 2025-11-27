# AI 聊天系统

一个功能完整的 AI 聊天系统，具有炫酷的 Gemini 风格界面和强大的后端支持。

## 🎨 项目特性

- **前端**：基于 React + TypeScript + Ant Design X，参考 Gemini 设计风格
- **后端**：使用 FastAPI + AutoGen 实现智能对话
- **流式输出**：支持 SSE（Server-Sent Events）协议的实时流式响应
- **现代化界面**：炫酷的渐变背景、优雅的动画效果、响应式设计

## 📁 项目结构

```
ai_study/
├── frontend/                 # 前端项目
│   ├── src/
│   │   ├── components/       # React 组件
│   │   │   ├── ChatInterface.tsx
│   │   │   └── ChatInterface.css
│   │   ├── App.tsx
│   │   ├── App.css
│   │   ├── main.tsx
│   │   └── index.css
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── backend/                  # 后端项目
│   ├── main.py              # FastAPI 主应用
│   ├── chat_service.py      # AutoGen 聊天服务
│   ├── requirements.txt     # Python 依赖
│   ├── env.example          # 环境变量示例
│   └── README.md
│
└── README.md                # 项目总文档
```

## 🚀 快速开始

### 前置要求

- Node.js 18+ 和 npm
- Python 3.10+
- OpenAI API Key

### 1. 克隆项目

```bash
cd ai_study
```

### 2. 启动后端

```bash
cd backend

# 创建并激活虚拟环境（推荐）
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
pip install autogen-agentchat autogen-ext[openai]

# 配置环境变量
# 将 env.example 复制为 .env 并填入您的 OpenAI API Key
copy env.example .env  # Windows
cp env.example .env    # Linux/Mac

# 编辑 .env 文件，填入您的 API Key
# OPENAI_API_KEY=your_actual_api_key_here

# 启动后端服务器
python main.py
```

后端将在 http://localhost:8000 启动

### 3. 启动前端

打开新的终端窗口：

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端将在 http://localhost:3000 启动

### 4. 开始使用

在浏览器中访问 http://localhost:3000，开始与 AI 助手对话！

## 🎯 功能特性

### 前端特性

- ✨ **炫酷界面**：参考 Gemini 的渐变背景和现代化设计
- 💬 **流式对话**：实时显示 AI 回复，支持打字动画效果
- 🎭 **优雅动画**：消息气泡淡入动画、旋转背景效果
- 📱 **响应式设计**：完美适配桌面和移动设备
- 🌙 **深色主题**：护眼的深色配色方案
- 🗑️ **清空对话**：一键清空聊天历史

### 后端特性

- 🤖 **AutoGen 集成**：使用微软 AutoGen 框架实现智能对话
- 📡 **SSE 流式输出**：支持服务器推送事件，实时返回响应
- ⚡ **异步处理**：基于 FastAPI 的异步架构，高性能
- 🔐 **CORS 支持**：安全的跨域资源共享配置
- 📝 **完整文档**：自动生成的 API 文档（Swagger UI）

## 📚 API 文档

后端启动后，访问以下地址查看 API 文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 主要 API 端点

1. **GET /api/health** - 健康检查
2. **POST /api/chat** - 非流式聊天
3. **POST /api/chat/stream** - 流式聊天（SSE）

## 🛠️ 技术栈

### 前端

- **React 18** - UI 框架
- **TypeScript** - 类型安全
- **Vite** - 构建工具
- **Ant Design X** - 对话气泡组件
- **Ant Design 5** - UI 组件库

### 后端

- **FastAPI** - Python Web 框架
- **AutoGen** - AI 代理框架
- **Uvicorn** - ASGI 服务器
- **SSE-Starlette** - 服务器推送事件
- **Pydantic** - 数据验证

## 🔧 配置说明

### 后端环境变量

在 `backend/.env` 文件中配置：

```env
# OpenAI API 配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1
MODEL_NAME=gpt-4o

# 服务器配置
HOST=0.0.0.0
PORT=8000

# CORS 配置
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### 前端代理配置

前端通过 Vite 代理转发请求到后端，配置在 `frontend/vite.config.ts`：

```typescript
server: {
  port: 3000,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    }
  }
}
```

## 📖 使用说明

1. **发送消息**：在输入框中输入消息，按回车或点击发送按钮
2. **查看响应**：AI 的回复会以流式方式逐字显示，带有打字动画效果
3. **清空对话**：点击右上角的"清空对话"按钮可以重置聊天记录
4. **滚动查看**：聊天记录会自动滚动到最新消息

## 🔍 故障排除

### 前端问题

1. **端口被占用**：修改 `vite.config.ts` 中的端口号
2. **依赖安装失败**：尝试删除 `node_modules` 和 `package-lock.json`，重新安装

### 后端问题

1. **AutoGen 导入错误**：
   ```bash
   pip install autogen-agentchat autogen-ext[openai]
   ```

2. **API Key 未设置**：检查 `.env` 文件是否存在且配置正确

3. **CORS 错误**：确保 `.env` 中的 `CORS_ORIGINS` 包含前端地址

## 📝 开发计划

- [ ] 支持多轮对话上下文
- [ ] 添加语音输入功能
- [ ] 支持 Markdown 渲染
- [ ] 添加代码高亮
- [ ] 支持图片上传
- [ ] 用户认证系统
- [ ] 对话历史保存

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

- [Ant Design X](https://x.ant.design/) - 优秀的 AI 对话组件库
- [AutoGen](https://microsoft.github.io/autogen/) - 微软的 AI 代理框架
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的 Python Web 框架

