# AGENTS.md - QBase AI 代理开发指南

本文档为在 QBase 仓库工作的 AI 编码代理提供指导。

## 项目概述

QBase 是一个本地知识库管理系统，基于 Vue 3 + Electron 构建。

### 当前版本 (v0.4)

- 工作区管理（添加/移除文件夹）
- 文件树导航（支持手动刷新）
- Markdown 预览（使用 XMarkdown，支持代码高亮、LaTeX、Mermaid）
- PDF 查看器（支持翻页、缩放）
- 音视频播放器（MP3, MP4, WebM 等）
- 三栏布局
- Electron 文件系统 API
- AI 助手对话面板 (BubbleList + Sender)
- LLM 配置管理 (本地/云端模型) + 测试连接功能
- 流式 AI 响应 (SSE)
- 多轮对话上下文管理
- 多会话管理（对话历史持久化）
- 全文搜索（UI + 内容片段）
- 智能闪卡生成（基于文档内容）
- Pinia 状态持久化 + Repository 抽象层

## 开发原则

### 代码质量原则

- **奥卡姆剃刀**: 优先选择简单方案
- **KISS**: 保持简单
- **YAGNI**: 避免过度工程化

### 语言偏好

- 使用中文编写文档
- 注释使用中文
- commit 消息使用中文

### 测试和质量保证

- 你只需要给出测试步骤，而不自动进行测试，测试由开发人员手动进行
- 安装依赖时，你只需要给出命令，而不自动执行

## 包管理器与命令

使用 **npm** 作为包管理器。主要命令：

```bash
npm install          # 安装依赖
npm run dev          # 启动 Vite 开发服务器
npm run build        # 生产构建
npm run test:unit    # 运行所有 Vitest 测试
npm run lint         # 运行 ESLint + Oxlint 并自动修复
npm run format       # Prettier 格式化代码
npm run ele          # 启动 Electron
npm run start        # 同时启动 Vite + Electron
```

### 运行单个测试

```bash
npm run test:unit -- src/__tests__/your-test.spec.js
npm run test:unit -- --watch  # 监听模式
```

## 代码风格指南

### 格式化规则

- 不使用分号
- 字符串使用单引号
- 行长度 100 字符
- 2 空格缩进
- 多行结构使用尾随逗号

### 导入规范

- 使用 ES 模块语法 (`import`/`export`)
- 路径别名 `@` 映射到 `./src`
- 导入分组：外部库 → 内部模块 → 组件/样式
- 不保留未使用的导入

### Vue 组件

- 使用 `<script setup>` 语法
- 使用 `<style scoped>` 作用域样式
- 组件文件名使用 PascalCase（如 `MyComponent.vue`）
- Props 和 emits 使用 TypeScript 或 JSDoc 定义

### 命名约定

| 类型 | 约定 | 示例 |
|------|------|------|
| 变量/函数 | camelCase | `loadFile` |
| 组件 | PascalCase | `MarkdownViewer.vue` |
| 常量 | UPPER_SNAKE_CASE | `API_BASE_URL` |
| Pinia store | useXxxStore | `useWorkspaceStore` |
| 测试文件 | *.spec.js | `App.spec.js` |

### 错误处理

- 异步操作使用 try/catch
- 提供有意义的中文错误信息
- 验证输入和边界情况

## 代码检查与测试工具

- **ESLint**: 扁平配置，含 Vue 和 Vitest 插件 (`eslint.config.js`)
- **Oxlint**: 快速正确性检查 (`.oxlintrc.json`)
- **Prettier**: 代码格式化 (`.prettierrc.json`)
- **Vitest**: 测试框架，配合 jsdom 和 `@vue/test-utils`

## 关键配置文件

所有应用文件在 `app/` 目录下：

- `app/package.json` - 依赖和脚本
- `app/eslint.config.js` - ESLint 配置
- `app/vitest.config.js` - Vitest 配置
- `app/.prettierrc.json` - Prettier 规则
- `app/.oxlintrc.json` - Oxlint 配置

## 文档维护

### 文档目录

项目根目录下的 `docs/` 文件夹：

```
docs/
├── README.md               # 文档入口
├── architecture/           # 架构设计（稳定层）
├── features/               # 功能实现（动态层）
├── implementation/         # 实施报告（项目层）
├── bugs/                   # 问题记录（项目层）
└── roadmap.md              # 项目路线图（项目层）
```

### 更新文档的时机

1. **完成新功能时**：更新对应功能文档的状态
2. **完成阶段时**：更新 roadmap.md 和 README.md
3. **实施重大变更时**：创建实施报告
4. **修复 Bug 时**：创建 bugs 记录

### 文档命名规范

```
features/<feature-name>.md           # 功能文档
implementation/<version>-complete.md # 实施报告
bugs/<date>-<bug-name>.md            # Bug 记录
```

### 状态标记

- ✅ 已完成
- 🔄 进行中
- 📋 已规划
- ⏳ 暂缓

## 开发工作流

1. `cd app` - 进入应用目录
2. 运行 `npm install` 安装依赖
3. `npm run dev` 启动 Vite 开发服务器
4. `npm run start` 启动完整 Electron 应用
5. 提交前运行 `npm run lint` 和 `npm run format`
6. 运行 `npm run test:unit` 验证测试通过

## 相关文档

- [CLAUDE.md](./CLAUDE.md) - 开发原则
- [docs/README.md](./docs/README.md) - 文档入口
- [docs/architecture/tech-stack.md](./docs/architecture/tech-stack.md) - 技术栈详情
