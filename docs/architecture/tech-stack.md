# QBase 技术栈

**版本**: v0.3
**更新日期**: 2026-02-25

## 核心技术

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue | ^3.5.28 | 前端框架 |
| Vue Router | ^5.0.2 | 路由管理 |
| Electron | ^40.6.0 | 桌面应用 |
| Pinia | ^3.0.4 | 状态管理 |
| Vite | ^7.3.1 | 构建工具 |

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
├── app/                    # 应用主目录
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
├── docs/                   # 项目文档
├── official_docs/          # 第三方库文档
├── AGENTS.md              # AI 代理开发指南
├── CLAUDE.md              # 开发原则
└── README.md              # 项目概述
```

## 开发命令

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

## 运行环境

- Node.js: ^20.19.0 || >=22.12.0
- 操作系统: Windows / macOS / Linux
