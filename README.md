# QBase

本地知识库管理系统，基于 Electron + Vue 3 + Element Plus 构建。

## 特性

- 📁 本地文件夹读取和管理
- 📝 Markdown 文档预览（支持代码高亮、数学公式、Mermaid）
- 🤖 AI 助手辅助知识管理
- 🔍 全文搜索（计划中）
- 🏷️ 标签和分类（计划中）

## 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue | ^3.5.28 | 前端框架 |
| Electron | ^40.6.0 | 桌面应用 |
| Pinia | ^3.0.4 | 状态管理 |
| Element Plus | ^2.13.2 | UI 组件库 |
| Element-Plus-X | ^1.3.98 | AI 体验组件 |
| Vite | ^7.3.1 | 构建工具 |
| Vitest | ^4.0.18 | 测试框架 |

## 快速开始

### 安装依赖

```bash
cd app
npm install
```

### 开发模式

```bash
npm run start    # 同时启动 Vite + Electron
npm run dev      # 仅启动 Vite
npm run ele      # 仅启动 Electron
```

### 构建

```bash
npm run build    # 构建生产版本
npm run dist     # 打包 Electron 应用
```

### 测试

```bash
npm run test:unit
```

### 代码规范

```bash
npm run lint    # 运行 lint
npm run format  # 格式化代码
```

## 开发进度

| 版本 | 状态 | 功能 |
|------|------|------|
| v0.1 | ✅ 已完成 | 核心文件浏览 |
| v0.2 | ✅ 已完成 | AI 助手 |
| v0.3 | 🔄 进行中 | 增强功能 |

详见 [项目路线图](./docs/roadmap.md)

## 项目结构

```
QBase/
├── app/                    # 应用主目录
│   ├── src/               # 源代码
│   │   ├── components/    # Vue 组件
│   │   ├── stores/        # Pinia stores
│   │   ├── repositories/  # 数据存储抽象层
│   │   ├── views/         # 页面视图
│   │   └── router/        # 路由配置
│   ├── electron/          # Electron 主进程
│   └── public/            # 静态资源
├── docs/                   # 项目文档
├── official_docs/          # 第三方库文档
├── AGENTS.md              # AI 代理开发指南
├── CLAUDE.md              # 开发原则
└── README.md              # 本文件
```

## 文档

- [文档入口](./docs/README.md)
- [系统架构](./docs/architecture/system-architecture.md)
- [技术栈](./docs/architecture/tech-stack.md)
- [项目路线图](./docs/roadmap.md)

## 开发原则

- **奥卡姆剃刀**: 简单方案优先
- **KISS**: 保持简单
- **YAGNI**: 避免过度工程化
- **中文**: 文档、注释、commit 消息使用中文

## License

MIT
