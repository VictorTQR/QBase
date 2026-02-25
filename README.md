# QBase

本地知识库管理系统，基于 Electron + Vue 3 + Element Plus 构建。

## 特性

- 📁 本地文件夹读取和管理
- 📝 Markdown 文档预览（支持代码高亮、数学公式、Mermaid）
- 🤖 AI 助手辅助知识管理（v0.2+）
- 🔍 全文搜索（v0.2+）
- 🏷️ 标签和分类（v0.3+）

## 技术栈

- **前端框架**: Vue 3 (Composition API + `<script setup>`)
- **桌面框架**: Electron
- **状态管理**: Pinia + pinia-plugin-persistedstate
- **UI 组件**: Element Plus + Element-Plus-X
- **HTTP 请求**: hook-fetch (支持流式 SSE)
- **构建工具**: Vite
- **测试框架**: Vitest

## 开发

### 安装依赖

```bash
cd app
npm install
```

### 开发模式

```bash
npm run start
```

### 构建

```bash
npm run build
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

### v0.1 (当前) - 核心文件浏览 ✅
- [x] 工作区管理（添加/移除文件夹）
- [x] 文件夹树导航
- [x] Markdown 预览（XMarkdown）
- [x] 三栏布局
- [x] Electron 文件系统 API

### v0.2 (进行中) - AI 助手
- [x] Agent 对话面板（BubbleList + Sender）
- [x] LLM 配置管理（本地/云端）
- [x] 基于文档的智能问答
- [x] Hook-Fetch 流式请求集成
- [ ] 基础全文搜索

### v0.3 (计划) - 增强功能
- [ ] 标签系统
- [ ] 搜索增强
- [ ] 内容组织推荐

## 项目结构

```
QBase/
├── app/
│   ├── src/
│   │   ├── components/       # Vue 组件
│   │   ├── stores/           # Pinia stores
│   │   ├── views/            # 页面视图
│   │   └── router/           # 路由配置
│   ├── electron/             # Electron 主进程
│   └── package.json
├── docs/                     # 文档
└── official_docs/            # 第三方库文档
```

## 开发原则

- **奥卡姆剃刀**: 简单方案优先
- **KISS**: 保持简单
- **YAGNI**: 避免过度工程化
- **中文**: 文档、注释、commit 消息使用中文

## License

MIT
