# QBase 系统架构

**版本**: v1.2
**更新日期**: 2026-04-06

## 核心定位

QBase 是一个本地知识库管理系统，核心特性：

- 本地文件夹读取和展示
- 支持多种文件格式（Markdown、PDF、音视频）
- Agent 能力辅助知识管理
- 向量搜索与全文搜索混合
- 渐进式迭代开发

## 整体架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         渲染进程 (Vue 3)                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │   Home.vue  │  │   Settings  │  │ ParseManagement │  │ 其他页面...  │  │
│  │  (三栏布局) │  │   (设置页)  │  │  (解析管理页)   │  │             │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  └─────────────┘  │
├─────────────────────────────────────────────────────────────────────────────┤
│                          Pinia 状态管理                                       │
│  ┌──────────┐ ┌──────────┐ ┌─────────┐ ┌─────────┐ ┌────────┐ ┌───────┐ │
│  │workspace │ │ document │ │  agent  │ │  parse  │ │ vector │ │ flash-│ │
│  │  store   │ │  store   │ │  store  │ │  store  │ │ store  │ │ card  │ │
│  └──────────┘ └──────────┘ └─────────┘ └─────────┘ └────────┘ └───────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────┐  ┌─────────────────────────────────────────┐  │
│  │ Electron API (preload)   │  │      FastAPI 后端服务                   │  │
│  │ - fileSystem             │  │  ┌──────────┐ ┌──────────┐ ┌───────┐ │  │
│  │ - search                 │  │  │ /api/    │ │ /api/    │ │ /ws/  │ │  │
│  │ - llm                    │  │  │ vector   │ │ audio    │ │ tasks │ │  │
│  │ - mineru                 │  │  └──────────┘ └──────────┘ └───────┘ │  │
│  │ - siliconflow            │  │  ┌─────────────────────────────────────┐ │  │
│  └──────────────────────────┘  │  │ LanceDB 向量数据库                  │ │  │
│                                 │  │ SQLite 解析存储                      │ │  │
│                                 │  └─────────────────────────────────────┘ │  │
│                                 └─────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 模块划分

| 模块 | 职责 | 状态 |
|------|------|------|
| workspace | 工作区管理（添加/移除文件夹） | ✅ |
| document | 文档加载和展示（多格式支持） | ✅ |
| agent | AI 助手对话（多会话、流式） | ✅ |
| repositories | 数据存储抽象层 | ✅ |
| search | 全文搜索 + 向量搜索 + 混合搜索 | ✅ |
| parse | 文档解析管理（MinerU、音频转录） | ✅ |
| vector | 向量索引和搜索（LanceDB） | ✅ |
| flashcard | 闪卡生成和管理 | ✅ |
| settings | 应用设置页面 | ✅ |
| papers | 论文管理（arXiv 搜索与本地保存） | ✅ |
| fileManagement | 新文件管理架构（.qbase 目录、文件哈希） | 🔄 |

## UI 布局

### 主页面三栏布局

| 栏位 | 宽度 | 功能 | 组件 |
|------|------|------|------|
| 左侧 | 25% | 文件夹树 + 解析管理入口 | Sidebar.vue |
| 中间 | 50% | 文档内容区（Markdown/PDF/音视频） | ContentPane.vue |
| 右侧 | 25% | Agent面板（对话/闪卡/思维导图/摘要） | AgentPanel.vue |

### 独立页面架构

| 页面 | 路由 | 功能 |
|------|------|------|
| 首页 | / | 三栏布局主界面 |
| 设置页 | /settings | LLM、PDF解析、向量存储配置 |
| 解析管理 | /parse-management | 解析队列、已解析文档、向量索引管理 |
| 论文管理 | /papers | arXiv 论文搜索与本地保存 |

### 组件结构

```
src/
├── api/                          # API 客户端
│   ├── backend.js               # FastAPI 后端通用客户端
│   ├── vectorBackend.js         # 向量搜索 API
│   ├── parseBackend.js        # 解析管理 API
│   ├── audioBackend.js        # 音频处理 API
│   ├── workspaceBackend.js     # 工作区 API
│   ├── fileBackend.js          # 文件操作 API
│   ├── derivativeBackend.js    # 衍生数据 API
│   └── papers.js               # 论文管理 API
├── components/
│   ├── Layout/
│   │   ├── MainLayout.vue       # 主布局容器
│   │   ├── Sidebar.vue          # 左侧文件夹树
│   │   ├── ContentPane.vue      # 中间内容区
│   │   ├── AgentPanel.vue       # 右侧Agent面板
│   │   ├── PanelNavSidebar.vue
│   │   ├── SettingsSidebar.vue
│   │   └── ParseSidebar.vue
│   ├── chat/                   # 对话相关
│   │   ├── ChatModule.vue
│   │   └── SessionSidebar.vue
│   ├── parse/                   # 解析管理组件
│   │   ├── ParseDocumentsView.vue
│   │   ├── ParseQueueView.vue
│   │   ├── ParseStatsView.vue
│   │   ├── ParseDetailsDrawer.vue
│   │   ├── FileManagementView.vue
│   │   ├── AudioParseView.vue
│   │   ├── KanbanView.vue
│   │   └── FileList.vue
│   ├── settings/               # 设置组件
│   │   ├── LlmSettings.vue
│   │   ├── VectorSettings.vue
│   │   ├── PdfParseSettings.vue
│   │   └── AudioParseSettings.vue
│   ├── flashcards/           # 闪卡组件
│   │   ├── FlashcardGenerator.vue
│   │   ├── FlashcardViewer.vue
│   │   ├── FlashcardPanel.vue
│   │   └── FlashcardSet.vue
│   ├── mindmap/              # 思维导图
│   │   └── MindmapGenerator.vue
│   ├── summary/              # 摘要生成
│   │   └── SummaryGenerator.vue
│   ├── shared/               # 共享组件
│   │   └── PanelHeader.vue
│   ├── DocumentViewer.vue    # 文档查看器（统一分发）
│   ├── MarkdownViewer.vue  # Markdown渲染组件
│   ├── PdfViewer.vue       # PDF查看器
│   ├── MediaViewer.vue     # 音视频播放器
│   ├── SearchPanel.vue    # 搜索面板（三种模式）
│   ├── WorkspaceCard.vue
│   ├── PaperList.vue
│   ├── PaperSearchDialog.vue
│   └── FrontmatterCard.vue
├── processors/                  # 文档处理器
│   └── parse/
├── repositories/                # 数据存储抽象层
├── router/                      # 路由配置
├── stores/                      # Pinia stores
│   ├── workspace.js
│   ├── document.js
│   ├── agent.js
│   ├── flashcard.js
│   ├── parse.js
│   ├── parseConfig.js
│   ├── vector.js
│   ├── search.js
│   ├── ui.js
│   ├── audio.js
│   └── fileManagement.js
├── utils/                       # 工具函数
├── vector/                      # 向量搜索相关
├── views/                       # 页面组件
│   ├── Home.vue
│   ├── WorkspaceSelector.vue
│   ├── Settings.vue
│   ├── ParseManagement.vue
│   └── PapersView.vue
└── __tests__/                   # Vitest 测试
```

## 数据流

### 文件浏览流程

```
用户选择文件夹 → Electron API → workspace store
                                    ↓
                              更新文件树
                                    ↓
用户点击文件 → Electron API → document store → 对应Viewer渲染
                              (Markdown/PDF/音视频)
```

### AI 对话流程

```
用户输入 → agent store → Hook-Fetch SSE → 流式响应
                              ↓
                         更新消息列表
                              ↓
                         BubbleList渲染
```

### 向量搜索流程

```
用户搜索 → search store → VectorBackendApi → FastAPI /api/vector/search
                                                              ↓
                                        LanceDB 相似度搜索 + 全文搜索
                                                              ↓
                                    混合排序结果返回前端展示
```

### 文档解析流程

```
添加解析 → parse store → TextExtractor/AudioTranscriber
                              ↓
                    本地提取 / MinerU / SiliconFlow
                              ↓
                    结果存储 IndexedDB
                              ↓
                    WebSocket 实时状态更新
```

### 向量索引流程

```
索引文档 → vector store → VectorBackendApi → FastAPI /api/vector/index
                                                              ↓
                                                    文本分块 + Embedding
                                                              ↓
                                                    LanceDB 存储向量
                                                              ↓
                                                    进度实时更新
```

## 数据持久化

使用多种存储方案：

| Store / 存储 | 持久化内容 | 技术 |
|-------------|-----------|------|
| workspace | folders（工作区列表） | Pinia persist + LocalStorage |
| agent | llmConfig（LLM配置）、会话历史 | Pinia persist + LocalStorage |
| parse | parseIndex（解析索引） | Pinia persist + LocalStorage |
| vector | indexedFiles（已索引文件列表） | Pinia persist + LocalStorage |
| flashcard | flashcardSets（闪卡集） | Pinia persist + LocalStorage |
| document_chunks | 文档向量分块 | LanceDB |
| parse_tasks | 解析任务记录 | SQLite (后端) |
| files | 文件元数据（v1.2 新增） | SQLite (后端) |
| derivatives | 衍生数据（v1.2 新增） | SQLite (后端) |
| papers | 论文信息 | SQLite (后端) |
| .qbase 目录 | 工作区元数据、缓存、生成文件 | 文件系统 |

## WebSocket 实时更新

**端点**:
- `ws://localhost:8000/ws/tasks/mineru` - MinerU 任务更新
- `ws://localhost:8000/ws/tasks/audio` - 音频任务更新

**特性**:
- 自动连接：页面加载时自动连接
- 实时同步：任务状态变更立即反映
- 无需刷新：任务列表和统计数据自动更新

## 错误处理

| 场景 | 处理方式 |
|------|----------|
| 文件夹读取失败 | 显示错误提示，跳过 |
| 文件读取失败 | 显示错误消息 |
| Markdown渲染失败 | 降级显示纯文本 |
| LLM请求失败 | 显示错误消息，停止打字效果 |
| 向量搜索失败 | 降级到全文搜索 |
| WebSocket连接失败 | 降级到轮询机制 |

## 安全考虑

- Electron 使用 preload 脚本暴露有限 API
- CSP 配置限制外部连接
- API Key 存储在 localStorage（后续可考虑加密存储）
- 后端 API 仅监听 localhost
