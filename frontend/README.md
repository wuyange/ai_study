# AI 聊天前端界面

基于 React + TypeScript + Ant Design X 构建的炫酷 AI 聊天界面，参考 Gemini 风格设计。

## 技术栈

- React 18
- TypeScript
- Vite
- Ant Design X (对话气泡组件)
- Ant Design 5

## 功能特性

- 🎨 炫酷的 Gemini 风格界面设计
- 💬 流式对话显示
- 🎭 优雅的动画效果
- 📱 响应式设计
- 🌙 深色主题

## 安装依赖

```bash
npm install
```

## 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:3000

## 构建生产版本

```bash
npm run build
```

## 项目结构

```
frontend/
├── src/
│   ├── components/
│   │   ├── ChatInterface.tsx    # 主聊天界面组件
│   │   └── ChatInterface.css    # 聊天界面样式
│   ├── App.tsx                   # 应用主组件
│   ├── App.css                   # 应用主样式
│   ├── main.tsx                  # 应用入口
│   └── index.css                 # 全局样式
├── index.html                    # HTML 模板
├── package.json                  # 项目配置
├── tsconfig.json                 # TypeScript 配置
└── vite.config.ts                # Vite 配置
```

