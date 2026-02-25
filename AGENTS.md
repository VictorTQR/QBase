# AGENTS.md - QBase AI 代理开发指南

本文档为在 QBase 仓库工作的 AI 编码代理提供指导。

## 项目概述

QBase 是一个本地知识库管理系统，基于 Vue 3 + Electron 构建：

- Vue 3 (Composition API，使用 `<script setup>`)
- Pinia 状态管理
- Vue Router 路由
- Electron 桌面打包
- Vite 构建工具
- Vitest 测试框架
- **Element Plus** UI 组件库
- **Element-Plus-X** AI 体验组件库（XMarkdown、Bubble 等）

### 当前版本 (v0.2)
- 工作区管理（添加/移除文件夹）
- 文件树导航
- Markdown 预览（使用 XMarkdown，支持代码高亮、LaTeX、Mermaid）
- 三栏布局
- Electron 文件系统 API
- **AI 助手对话面板** (BubbleList + Sender)
- **LLM 配置管理** (本地/云端模型)
- **流式 AI 响应** (hook-fetch + SSE)
- **Pinia 状态持久化** (工作区配置、LLM 设置)

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

运行单个测试文件：

```bash
npm run test:unit -- src/__tests__/your-test.spec.js
```

监听模式运行测试：

```bash
npm run test:unit -- --watch
```

## 代码风格指南

### 通用原则（来自 CLAUDE.md）

- **奥卡姆剃刀**: 优先选择简单方案
- **KISS**: 保持简单
- **YAGNI**: 避免过度工程化
- **中文**: 所有注释、文档、commit 消息使用中文

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

- 变量和函数：camelCase
- 组件：PascalCase
- 常量：UPPER_SNAKE_CASE
- Pinia store：useXxxStore
- 测试文件：`__tests__` 目录下的 `*.spec.js`

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
- `CLAUDE.md` - 项目指南（中文）

## 开发工作流

1. `cd app` - 进入应用目录
2. 运行 `npm install` 安装依赖
3. `npm run dev` 启动 Vite 开发服务器
4. `npm run start` 启动完整 Electron 应用
5. 提交前运行 `npm run lint` 和 `npm run format`
6. 运行 `npm run test:unit` 验证测试通过

## Agent/Cursor/Copilot 规则

未找到现有的 Cursor 或 Copilot 规则文件。请遵循：

- 本 AGENTS.md 中的指南
- CLAUDE.md 中的原则
- 代码库中的现有代码模式
