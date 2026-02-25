# QBase 系统架构

**版本**: v0.3
**更新日期**: 2026-02-25

## 核心定位

QBase 是一个本地知识库管理系统，核心特性：

- 本地文件夹读取和展示
- 前期不提供编辑功能
- Agent 能力辅助知识管理
- 渐进式迭代开发

## 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    渲染进程 (Vue 3)                          │
├──────────────────┬──────────────────┬───────────────────────┤
│   左栏           │     中栏         │      右栏              │
│  文件树导航      │   Markdown预览   │    Agent对话面板       │
├──────────────────┴──────────────────┴───────────────────────┤
│                    Pinia 状态管理                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐     │
│  │ workspace   │  │  document   │  │    agent        │     │
│  │   store     │  │   store     │  │    store        │     │
│  └─────────────┘  └─────────────┘  └─────────────────┘     │
├─────────────────────────────────────────────────────────────┤
│                    Electron API (preload)                    │
│  - fileSystem: 读取文件/文件夹                                │
│  - search: 全文搜索                                           │
│  - llm: LLM调用                                               │
└─────────────────────────────────────────────────────────────┘
```

## 模块划分

| 模块 | 职责 | 状态 |
|------|------|------|
| workspace | 工作区管理（添加/移除文件夹） | ✅ |
| document | 文档加载和展示 | ✅ |
| agent | AI 助手对话 | ✅ |
| repositories | 数据存储抽象层 | ✅ |
| search | 全文搜索 | 📋 |

## UI 布局

### 三栏布局

| 栏位 | 宽度 | 功能 | 组件 |
|------|------|------|------|
| 左侧 | 25% | 文件夹树 | el-tree |
| 中间 | 50% | Markdown内容 | XMarkdown |
| 右侧 | 25% | Agent面板 | BubbleList + Sender |

### 组件结构

```
src/
├── components/
│   ├── Layout/
│   │   ├── MainLayout.vue      # 主布局容器
│   │   ├── Sidebar.vue         # 左侧文件夹树
│   │   ├── ContentPane.vue     # 中间内容区
│   │   ├── AgentPanel.vue      # 右侧Agent面板
│   │   └── SessionSidebar.vue  # 会话列表侧边栏
│   ├── LlmConfigDialog.vue     # LLM配置对话框
│   └── MarkdownViewer.vue      # Markdown渲染组件
├── stores/
│   ├── workspace.js            # 工作区状态
│   ├── document.js             # 文档状态
│   └── agent.js                # Agent状态
├── repositories/
│   ├── SessionRepository.js              # 会话存储抽象接口
│   └── LocalStorageSessionRepository.js  # localStorage 实现
├── views/
│   └── Home.vue                # 首页
├── router/
│   └── index.js                # 路由配置
└── utils/
    └── api.js                  # Hook-Fetch API配置
```

## 数据流

### 文件浏览流程

```
用户选择文件夹 → Electron API → workspace store
                                    ↓
                              更新文件树
                                    ↓
用户点击文件 → Electron API → document store → XMarkdown渲染
```

### AI 对话流程

```
用户输入 → agent store → Hook-Fetch SSE → 流式响应
                              ↓
                         更新消息列表
                              ↓
                         BubbleList渲染
```

## 数据持久化

使用 `pinia-plugin-persistedstate` 插件：

| Store | 持久化内容 |
|-------|-----------|
| workspace | folders（工作区列表） |
| agent | llmConfig（LLM配置） |

## 错误处理

| 场景 | 处理方式 |
|------|----------|
| 文件夹读取失败 | 显示错误提示，跳过 |
| 文件读取失败 | 显示错误消息 |
| Markdown渲染失败 | 降级显示纯文本 |
| LLM请求失败 | 显示错误消息，停止打字效果 |

## 安全考虑

- Electron 使用 preload 脚本暴露有限 API
- CSP 配置限制外部连接
- API Key 存储在 localStorage（后续可考虑加密存储）
