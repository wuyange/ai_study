# 多会话 AI 聊天系统使用指南

## 📋 功能概述

本系统已成功升级为支持多会话管理的完整 AI 聊天应用，具有以下核心功能：

### ✨ 主要特性

1. **多会话管理**
   - 创建、切换、重命名、删除会话
   - 会话列表实时更新
   - 自动按更新时间排序

2. **历史记录**
   - 所有对话永久保存在 SQLite 数据库
   - 切换会话时自动加载历史消息
   - 支持上下文连贯的多轮对话（最近 20 条消息作为上下文）

3. **智能标题生成**
   - 发送第一条消息后自动生成会话标题
   - 使用 AI 生成简洁准确的标题

4. **会话导出**
   - 支持 JSON 格式（结构化数据，适合备份）
   - 支持 Markdown 格式（文本格式，适合阅读）

5. **炫酷 UI**
   - Gemini 风格的现代化界面
   - 流畅的动画和交互效果
   - 响应式设计，支持移动端

## 🚀 启动系统

### 方式一：一键启动（推荐）

```bash
start_all.bat
```

### 方式二：分别启动

**启动后端：**
```bash
start_backend.bat
```

**启动前端：**
```bash
start_frontend.bat
```

### 访问地址

- **前端界面**: http://localhost:3000
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

## 📖 使用说明

### 1. 创建新会话

1. 点击左侧边栏顶部的 **"新建会话"** 按钮
2. 系统自动创建一个名为 "新对话" 的会话
3. 发送第一条消息后，AI 会自动生成合适的标题

### 2. 发送消息

1. 在输入框中输入消息
2. 按 Enter 或点击发送按钮
3. AI 会实时流式回复
4. 消息会自动保存到数据库

### 3. 切换会话

1. 点击左侧边栏中的任意会话
2. 系统自动加载该会话的历史消息
3. 继续对话时会带上最近 20 条消息作为上下文

### 4. 重命名会话

1. 将鼠标悬停在会话项上
2. 点击右侧出现的 **"···"** 按钮
3. 选择 **"重命名"**
4. 输入新标题并确认

### 5. 导出会话

1. 将鼠标悬停在会话项上
2. 点击 **"···"** → **"导出"**
3. 选择导出格式（JSON 或 Markdown）
4. 文件自动下载到本地

### 6. 删除会话

1. 将鼠标悬停在会话项上
2. 点击 **"···"** → **"删除"**
3. 确认删除操作
4. 会话及其所有消息将被永久删除

## 🗄️ 数据库说明

### 数据存储

- **位置**: `backend/data/chat.db`
- **类型**: SQLite
- **表结构**:
  - `sessions`: 会话表（id, title, created_at, updated_at）
  - `messages`: 消息表（id, session_id, role, content, timestamp）

### 备份数据

**方法一：复制数据库文件**
```bash
copy backend\data\chat.db backup_chat.db
```

**方法二：使用导出功能**
- 逐个导出会话为 JSON 文件

### 恢复数据

**恢复数据库文件：**
```bash
copy backup_chat.db backend\data\chat.db
```

## 🛠️ API 端点

### 会话管理

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/sessions` | 创建新会话 |
| GET | `/api/sessions` | 获取所有会话 |
| GET | `/api/sessions/{id}` | 获取单个会话 |
| PUT | `/api/sessions/{id}/title` | 更新会话标题 |
| DELETE | `/api/sessions/{id}` | 删除会话 |
| GET | `/api/sessions/{id}/export` | 导出会话 |

### 消息管理

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/sessions/{id}/messages` | 获取会话消息 |
| POST | `/api/sessions/{id}/chat` | 发送消息（非流式） |
| POST | `/api/sessions/{id}/chat/stream` | 发送消息（流式） |
| POST | `/api/sessions/{id}/generate-title` | 生成标题 |

## 🔧 技术架构

### 后端技术栈

- **框架**: FastAPI
- **数据库**: SQLite + SQLAlchemy (异步)
- **AI 框架**: AutoGen
- **流式输出**: Server-Sent Events (SSE)

### 前端技术栈

- **框架**: React + TypeScript
- **构建工具**: Vite
- **UI 库**: Ant Design 6.x + Ant Design X
- **状态管理**: React Hooks

### 关键实现

1. **上下文管理**
   - 每次发送消息时携带最近 20 条历史消息
   - 后端将历史转换为对话上下文传递给 AI

2. **流式响应**
   - 使用 SSE 协议实时传输 AI 回复
   - 前端逐字符渲染，提升用户体验

3. **自动标题生成**
   - 第一条消息发送后自动触发
   - 使用独立的 LLM 调用生成 10-20 字标题

4. **异步数据库操作**
   - 使用 `aiosqlite` + SQLAlchemy async engine
   - 流式响应完成后批量保存消息

## 🐛 故障排除

### 后端启动失败

1. 检查虚拟环境是否激活
2. 检查 `.env` 文件是否配置正确
3. 确保安装了所有依赖：
   ```bash
   cd backend
   ..\backend\venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

### 前端连接失败

1. 确保后端已启动（http://localhost:8000）
2. 检查浏览器控制台错误信息
3. 确认 Vite 代理配置正确

### 数据库错误

1. 确保 `backend/data/` 目录存在
2. 重新初始化数据库：
   ```bash
   .\backend\venv\Scripts\python.exe backend/init_db.py
   ```

### AI 回复异常

1. 检查 OpenAI API Key 是否正确配置
2. 检查网络连接
3. 查看后端日志输出

## 📝 开发说明

### 添加新的 API 端点

1. 在 `backend/models.py` 中定义 Pydantic 模型
2. 在 `backend/db_operations.py` 中实现数据库操作
3. 在 `backend/main.py` 中添加路由

### 扩展前端功能

1. 在 `frontend/src/api/client.ts` 中添加 API 调用
2. 创建新的 Hook（如需要）
3. 实现 UI 组件

### 数据库迁移

如需修改数据库结构：

1. 修改 `backend/database.py` 中的模型
2. 手动编写迁移脚本或使用 Alembic
3. 备份现有数据
4. 执行迁移

## 🎯 未来扩展建议

1. **用户认证**: 添加登录/注册功能，支持多用户
2. **会话搜索**: 按标题或内容搜索会话
3. **消息编辑**: 支持编辑和重新发送消息
4. **附件支持**: 支持发送图片、文件等
5. **会话分组**: 按标签或文件夹组织会话
6. **快捷指令**: 支持自定义快捷指令和模板
7. **主题切换**: 支持深色/浅色模式切换
8. **云端同步**: 支持数据云端备份和多设备同步

## 📞 技术支持

如遇到问题，请检查：

1. 后端日志：启动后端时的控制台输出
2. 浏览器控制台：按 F12 打开开发者工具
3. 数据库状态：检查 `backend/data/chat.db` 是否存在

---

**版本**: 2.0.0 (多会话版本)  
**更新日期**: 2024年12月  
**开发状态**: ✅ 完成并可用

