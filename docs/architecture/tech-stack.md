# QBase 技术栈

**版本**: v1.2
**更新日期**: 2026-04-06

## 前端技术

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue | ^3.5.28 | 前端框架 |
| Vue Router | ^5.0.2 | 路由管理 |
| Electron | ^40.6.0 | 桌面应用 |
| Pinia | ^3.0.4 | 状态管理 |
| Element Plus | ^2.13.2 | UI 组件库 |
| Element-Plus-X | ^1.3.98 | AI 体验组件 |
| Vite | ^7.3.1 | 构建工具 |
| Vitest | ^4.0.18 | 单元测试 |
| Oxlint | ~1.47.0 | 快速 lint |
| ESLint | ^10.0.1 | 代码检查 |
| Prettier | 3.8.1 | 代码格式化 |

## 后端技术

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | >=3.12 | 编程语言 |
| FastAPI | >=0.135.1 | Web 框架 |
| Uvicorn | >=0.41.0 | ASGI 服务器 |
| SQLAlchemy | >=2.0 | ORM 框架 |
| aiosqlite | - | 异步 SQLite 驱动 |
| LanceDB | - | 向量数据库 |
| HTTPX / aiohttp | - | 异步 HTTP 客户端 |
| Pydantic | - | 数据验证 |
| pydantic-settings | >=2.0.0 | 配置管理 |
| python-multipart | >=0.0.9 | 文件上传支持 |
| aiofiles | >=24.1.0 | 异步文件操作 |
| Loguru | >=0.7.3 | 日志记录 |
| ffmpeg | - | 音频处理 |
| pyarrow | - | 数据处理 |
| uv | - | 包管理器 |

## UI 组件库

| 组件库 | 版本 | 用途 |
|--------|------|------|
| Element Plus | ^2.13.2 | 基础 UI 组件 |
| Element-Plus-X | ^1.3.98 | AI 体验组件 |

### Element-Plus-X 组件使用

| 组件 | 用途 | 版本引入 |
|------|------|----------|
| XMarkdown | Markdown渲染（代码高亮、公式、mermaid） | v0.1 |
| Bubble | 对话气泡 | v0.2 |
| BubbleList | 气泡列表 | v0.2 |
| Sender | 输入框 | v0.2 |

## 网络请求

使用原生 `fetch` API 配合 SSE 流式处理：

- 支持 OpenAI 兼容 API
- 支持 Ollama 本地模型
- 流式响应处理

## 开发工具

| 工具 | 版本 | 用途 |
|------|------|------|
| Vitest | ^4.0.18 | 单元测试 |
| ESLint | ^10.0.1 | 代码检查 |
| Oxlint | ~1.47.0 | 快速 lint |
| Prettier | 3.8.1 | 代码格式化 |

## 代码规范

### 格式化规则

- 不使用分号
- 字符串使用单引号
- 行长度 100 字符
- 2 空格缩进
- 多行结构使用尾随逗号

### Vue 组件规范

- 使用 `<script setup>` 语法
- 使用 `<style scoped>` 作用域样式
- 组件文件名使用 PascalCase

### 命名约定

| 类型 | 约定 | 示例 |
|------|------|------|
| 变量/函数 | camelCase | `loadFile` |
| 组件 | PascalCase | `MarkdownViewer.vue` |
| 常量 | UPPER_SNAKE_CASE | `API_BASE_URL` |
| Pinia store | useXxxStore | `useWorkspaceStore` |
| 测试文件 | *.spec.js | `App.spec.js` |

## 项目结构

```
QBase/
├── app/                    # Electron + Vue 3 前端应用
│   ├── src/               # 源代码
│   │   ├── components/    # Vue 组件
│   │   ├── stores/        # Pinia stores
│   │   ├── repositories/  # 数据存储抽象层
│   │   ├── views/         # 页面视图
│   │   ├── router/        # 路由配置
│   │   ├── utils/         # 工具函数
│   │   └── __tests__/     # 测试文件
│   ├── electron/          # Electron 主进程
│   └── public/            # 静态资源
├── backend/                # FastAPI 后端服务
│   ├── src/               # 源代码
│   │   ├── api/           # API 路由
│   │   ├── mineru/        # MinerU 相关模块
│   │   ├── models/        # 数据模型
│   │   ├── utils/         # 工具函数
│   │   └── config.py      # 配置管理
│   ├── main.py            # 主应用入口
│   └── pyproject.toml     # Python 项目配置
├── docs/                   # 项目文档
├── official_docs/          # 第三方库文档
├── AGENTS.md              # AI 代理开发指南
├── CLAUDE.md              # 开发原则
└── README.md              # 项目概述
```

## 前端开发命令

```bash
cd app

npm install          # 安装依赖
npm run dev          # 启动 Vite 开发服务器
npm run ele          # 启动 Electron
npm run start        # 同时启动 Vite + Electron
npm run build        # 构建生产版本
npm run test:unit    # 运行测试
npm run lint         # 运行 lint
npm run format       # 格式化代码
```

## 后端开发命令

```bash
cd backend

uv pip install .     # 安装依赖
cp .env.example .env # 配置环境变量（填入 MINERU_API_KEY）
uv run python -m uvicorn main:app --reload  # 启动开发服务器

# 访问 API 文档
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

## 运行环境

- Node.js: ^20.19.0 || >=22.12.0
- 操作系统: Windows / macOS / Linux
