# QBase 项目路线图

**更新日期**: 2026-03-02

## 版本概览

| 版本 | 状态 | 主题 | 发布日期 |
|------|------|------|----------|
| v0.1 | ✅ 已完成 | 核心文件浏览 | 2026-02-25 |
| v0.2 | ✅ 已完成 | AI 助手 | 2026-02-25 |
| v0.3 | ✅ 已完成 | 增强功能 | 2026-02-25 |
| v0.4 | ✅ 已完成 | 文件格式+闪卡 | 2026-02-25 |
| v0.5 | ✅ 已完成 | 智能生成与UI优化 | 2026-02-26 |
| v0.6 | ✅ 核心架构完成 | 智能体能力增强 | 2026-02-27 |
| v0.7 | ✅ 已完成 | 文档解析管理与文本提取 | 2026-02-27 |
| v0.8 | ✅ 已完成 | 应用设置页面与 PDF 解析策略 | 2026-03-02 |
| v0.9 | ✅ 已完成 | 解析管理 UI 重构与增强 | 2026-03-02 |

---

## v0.1 - 核心文件浏览 ✅

**状态**: 已完成
**发布日期**: 2026-02-25

### 功能列表

| 功能 | 状态 | 说明 |
|------|------|------|
| 工作区管理 | ✅ | 添加/移除本地文件夹 |
| 文件树导航 | ✅ | 左侧树形展示 |
| Markdown 预览 | ✅ | XMarkdown 渲染 |
| 三栏布局 | ✅ | 响应式布局 |
| Electron API | ✅ | 文件系统操作 |

### 技术实现

- Element Plus + Element-Plus-X 配置
- Workspace Store（工作区管理）
- Document Store（文档加载）
- Electron preload API

### 相关文档

- [实施报告](./implementation/v0.1-complete.md)

---

## v0.2 - AI 助手 ✅

**状态**: 已完成
**发布日期**: 2026-02-25

### 功能列表

| 功能 | 状态 | 说明 |
|------|------|------|
| Agent 对话面板 | ✅ | BubbleList + Sender |
| LLM 配置管理 | ✅ | 本地/云端模型 |
| 流式响应 | ✅ | SSE 处理 |
| 基于文档问答 | ✅ | 上下文包含 |
| 状态持久化 | ✅ | Pinia persist |

### 技术实现

- Agent Store（对话管理）
- LlmConfigDialog 组件
- 流式请求处理
- UUID 消息 ID 生成

### Bug 修复

- [消息 ID 重复问题](./bugs/2026-02-25-message-id-duplicate.md)

### 相关文档

- [实施报告](./implementation/v0.2-complete.md)
- [AI 助手功能](./features/ai-assistant.md)

---

## v0.3 - 增强功能 ✅

**状态**: 已完成
**发布日期**: 2026-02-25

### 功能列表

| 功能 | 状态 | 说明 |
|------|------|------|
| 对话历史持久化 | ✅ | 多会话管理 + Repository 抽象 |
| 测试连接功能 | ✅ | LLM 连接测试 |
| 多轮对话上下文 | ✅ | 上下文管理 |
| 手动刷新功能 | ✅ | 工作区文件树手动刷新 |
| 标签系统 | ⏳ | 文件标签分类（暂缓） |
| 搜索增强 | ✅ | 全文搜索 UI + 内容片段 |
| 文件夹监听 | ⏳ | 实时更新（暂缓） |

### 已完成部分

**对话历史持久化** (2026-02-25):
- Repository 抽象层设计
- LocalStorage 存储实现
- 多会话管理（创建/切换/删除/重命名）
- 会话列表侧边栏 UI
- 数据持久化和恢复

**测试连接功能** (2026-02-25):
- agent store 新增 testConnection 函数
- LLM 配置对话框添加测试按钮
- 支持加载状态和成功/失败提示
- 使用 ElMessage 显示测试结果

**多轮对话上下文** (2026-02-25):
- 修改 sendMessage 函数
- 在添加新消息前获取历史消息
- 构建完整的 messages 数组：[system, ...历史消息, 当前用户消息]
- 支持真正的多轮对话

**手动刷新功能** (2026-02-25):
- 在工作区侧边栏添加刷新按钮
- 支持 loading 状态防止重复点击
- 点击按钮手动刷新文件树
- 文件夹监听功能暂缓实现

**相关文档**:
- [实施报告](./implementation/v0.3-complete.md)

### 技术规划

- 搜索索引优化
- 本地存储方案
- 文件监听 API

### 相关文档

- [实施报告](./implementation/v0.3-complete.md)

---

## v0.4 - 文件格式增强与闪卡生成 ✅

**状态**: 已完成
**发布日期**: 2026-02-25

### 功能列表

| 功能 | 状态 | 说明 |
|------|------|------|
| PDF 查看器 | ✅ | pdfjs-dist 渲染，支持翻页缩放 |
| 音视频播放器 | ✅ | HTML5 原生播放器 |
| 多格式文件树 | ✅ | 支持 PDF、音频、视频显示 |
| 闪卡生成 | ✅ | 基于 LLM 的智能闪卡生成 |
| 闪卡查看器 | ✅ | 翻转动画，标记掌握 |
| 闪卡集管理 | ✅ | 持久化存储 |
| 艾宾浩斯复习 | ⏳ | 后续版本 |
| Anki 导出 | ⏳ | 后续版本 |

### 已完成部分

**文件格式增强 (2026-02-25)**:
- PDF 查看器组件（PdfViewer.vue）
- 音视频播放器组件（MediaViewer.vue）
- 统一文档分发器（DocumentViewer.vue）
- Electron 二进制文件读取 API
- 支持的格式：PDF, MP3, WAV, OGG, M4A, FLAC, MP4, WebM, MOV

**闪卡生成功能 (2026-02-25)**:
- Repository 抽象层设计
- LocalStorage 闪卡存储实现
- Flashcard Store 状态管理
- 提示词模板设计
- 闪卡生成器组件（支持 5-20 张）
- 闪卡查看器（翻转动画、前后翻页）
- 闪卡集列表管理
- AgentPanel 双模式切换（对话/闪卡）

### 相关文档

- [实施计划](./plans/2026-02-25-file-format-enhancement.md)
- [实施报告](./implementation/v0.4-complete.md)

---

## v0.5 - 智能生成与UI优化 ✅

**状态**: 已完成
**发布日期**: 2026-02-26

### 功能列表

| 功能 | 状态 | 说明 |
|------|------|------|
| 思维导图生成 | ✅ | 基于文档内容的智能思维导图生成 |
| 摘要生成 | ✅ | 自动提取文档核心内容生成摘要 |
| 独立标签页架构 | ✅ | 思维导图和摘要各有独立标签页 |
| 结果预览 | ✅ | 实时预览生成结果 |
| UI 重构 | ✅ | 移除重复功能，优化用户体验 |

### 已完成部分

**智能生成功能增强** (2026-02-26):
- 思维导图生成提示模板设计
- 摘要生成提示模板设计
- Agent Store 新增 generateMindmap 和 generateSummary 方法
- SVG 格式思维导图预览

**UI 重构与优化** (2026-02-26):
- 创建独立的 MindmapGenerator 和 SummaryGenerator 组件
- AgentPanel 从 3 个标签页扩展为 4 个标签页
- 标签页：对话、闪卡、思维导图、摘要
- 移除重复的闪卡生成入口
- 代码结构模块化，职责更清晰

### 相关文档

- [实施报告](./implementation/0.5-ai-generation-enhancement.md)
- [重构计划](./plans/2026-02-26-sidebar-refactor.md)

---

## v0.6 - 智能体能力增强（核心架构完成）✅

**状态**: 核心架构完成
**发布日期**: 2026-02-27

### 功能列表

| 功能 | 状态 | 说明 |
|------|------|------|
| DocumentProcessor 接口 | ✅ | 统一文档处理接口层（预埋架构） |
| MinerUProcessor 实现 | ✅ | MinerU API 集成 |
| VectorStore 接口 | ✅ | 统一向量存储接口层（预埋架构） |
| MemoryVectorStore 实现 | ✅ | 内存向量索引 + 余弦相似度 |
| Electron IPC 集成 | ✅ | MinerU + SiliconFlow IPC 处理器 |
| 配置扩展 | ✅ | MinerU + SiliconFlow 配置管理 |
| 配置 UI | ✅ | LlmConfigDialog 新增 Tab 页 |

### 已完成部分

**架构层预埋** (2026-02-27):
- DocumentProcessor 统一接口定义
- VectorStore 统一接口定义
- 支持后期无缝切换本地实现

**Electron 主进程集成** (2026-02-27):
- preload.js 新增 mineru 和 siliconflow 命名空间
- main.js 新增完整的 IPC 处理器
- 支持文件上传、任务轮询、结果下载

**UI 配置** (2026-02-27):
- agent.js 新增 mineru 和 siliconflow 配置
- LlmConfigDialog 新增 3 个 Tab 页（LLM、MinerU、SiliconFlow）

### 核心架构

- **B+ 架构**: MVP 快速迭代 + 预埋统一接口层
- **云端先行**: MinerU + SiliconFlow API
- **本地跟进**: 后期支持 transformers.js / Ollama

### 相关文档

- [设计文档](./plans/2026-02-27-v0.6-ai-agent-enhancement-design.md)
- [实施计划](./plans/2026-02-27-v0.6-implementation.md)

---

## v0.7 - 文档解析管理 ✅

**状态**: 已完成
**发布日期**: 2026-02-27

### 功能列表

| 功能 | 状态 | 说明 |
|------|------|------|
| 左侧标签切换 | ✅ | 文件树/解析管理双标签页 |
| 解析状态管理 | ✅ | 待解析/解析中/已完成/失败状态 |
| 统计概览 | ✅ | 解析进度、数量统计展示 |
| 解析队列 | ✅ | 展示各状态任务列表 |
| 文档列表 | ✅ | 文件夹树形式展示解析状态 |
| 解析详情 | ✅ | 查看解析结果、重新解析 |
| 混合存储方案 | ✅ | LocalStorage + IndexedDB (Dexie.js) |
| Repository 抽象 | ✅ | 数据访问层封装 |
| 文本提取 | ✅ | Markdown + PDF 本地提取，混合策略 |
| 音频转录 | 📋 | 待实现（占位文件已创建） |
| 向量化表示 | 📋 | 待实现（占位文件已创建） |

### 已完成部分

**UI 框架与布局 (2026-02-27)**:
- Sidebar.vue 改造为双标签页设计
- ParseManager 主组件整合所有子组件
- ParseStats 统计概览组件
- ParseQueue 解析队列组件
- ParseDocumentList 文档列表组件
- ParseDetails 解析详情组件

**状态管理与存储 (2026-02-27)**:
- useParseStore 状态管理（Pinia）
- IndexedDBRepository 封装（Dexie.js）
- ParseIndexRepository LocalStorage 存储
- 混合存储方案落地

**架构预埋 (2026-02-27)**:
- TextExtractor 占位文件
- AudioTranscriber 占位文件
- Vectorizer 占位文件
- 为后续功能扩展预留接口

**文本提取功能 (2026-02-27)**:
- TextExtractor 核心类实现
- Markdown 文本提取（去除 frontmatter）
- PDF 本地文本提取（基于 pdfjs-dist）
- 混合策略：优先本地，可选云端 MinerU 降级
- 解析状态管理集成
- IndexedDB 存储提取结果
- Sidebar 右键菜单"添加到解析"
- ParseManager 批量解析功能
- ParseDetails 提取文本预览

### 相关文档

- [设计文档](./plans/2026-02-27-parse-manager-design.md)
- [实施计划](./plans/2026-02-27-parse-manager-implementation.md)
- [文本提取设计文档](./plans/2026-02-27-text-extraction-design.md)
- [文本提取实施计划](./plans/2026-02-27-text-extraction-implementation.md)
- [实施报告](./implementation/v0.7-text-extraction-complete.md)

---

## v0.8 - 应用设置页面与 PDF 解析策略 ✅

**状态**: 已完成
**发布日期**: 2026-03-02

### 功能列表

| 功能 | 状态 | 说明 |
|------|------|------|
| 统一设置页面 | ✅ | 独立 /settings 路由页面 |
| 设置页面导航 | ✅ | 左侧导航栏（LLM、PDF 解析、向量存储） |
| 设置模块拆分 | ✅ | LlmSettings、PdfParseSettings、VectorSettings |
| PDF 解析配置 | ✅ | MinerU 高级选项（公式/表格/OCR/语言） |
| MinerU 连接测试 | ✅ | 测试连接功能 |
| MinerU API 增强 | ✅ | 完整 API Payload 支持 |
| 错误处理增强 | ✅ | 友好中文提示 + 修复建议 |
| 入口清理 | ✅ | 移除 AgentPanel 设置按钮，删除 LlmConfigDialog |

### 已完成部分

**统一设置页面 (2026-03-02)**:
- 新增 Settings.vue 主页面（二栏布局）
- 新增 SettingsSidebar.vue 导航组件
- 路由配置 /settings
- MainLayout Header 添加设置图标按钮
- 左上角返回首页功能

**设置模块拆分 (2026-03-02)**:
- LlmSettings.vue - LLM 配置（API 类型、Base URL、Key、Model）
- PdfParseSettings.vue - PDF 解析配置（MinerU 高级选项）
- VectorSettings.vue - 向量存储配置（SiliconFlow）

**MinerU 增强 (2026-03-02)**:
- API Payload 完善（enable_formula、enable_table、is_ocr、language）
- 自定义 Base URL 支持
- 测试连接 IPC 处理器
- 增强错误处理（分类错误 + 中文提示）

**旧代码清理 (2026-03-02)**:
- 从 PanelHeader 移除设置按钮
- 从 AgentPanel 移除 LlmConfigDialog 引用
- 删除 LlmConfigDialog.vue 文件

### 相关文档

- [实施报告](./implementation/v0.8-settings-page-complete.md)
- [MinerU 增强计划](./plans/2026-03-02-mineru-enhancements.md)

---

## v0.9 - 解析管理 UI 重构与增强 ✅

**状态**: 已完成
**发布日期**: 2026-03-02

### 功能列表

| 功能 | 状态 | 说明 |
|------|------|------|
| 独立全屏页面 | ✅ | 解析管理从标签页升级为独立页面 |
| 左侧功能导航 | ✅ | 队列管理/已解析文档/解析统计 |
| 队列管理增强 | ✅ | 三标签页布局（解析中/待解析/失败） |
| 文档搜索筛选 | ✅ | 关键词搜索 + 状态筛选器 |
| 卡片网格布局 | ✅ | 更美观的文档展示 |
| 详情抽屉 | ✅ | 右侧抽屉展示完整信息 |
| 可视化统计 | ✅ | 统计卡片 + 状态分布条 |
| 侧边栏入口 | ✅ | 底部永久"解析管理"按钮 |
| 字段统一 | ✅ | 统一使用 `fileType` 字段 |

### 已完成部分

**页面架构重构 (2026-03-02)**:
- 创建 ParseManagement.vue 独立页面
- 采用类似设置页面的全屏布局
- 顶部导航栏（返回按钮 + 标题 + 操作按钮）
- 左侧功能导航 + 右侧内容区域
- 路由配置 `/parse-management`

**组件模块化 (2026-03-02)**:
- ParseSidebar.vue - 左侧功能导航
- ParseQueueView.vue - 队列管理（标签页分类）
- ParseDocumentsView.vue - 已解析文档（搜索筛选）
- ParseStatsView.vue - 解析统计（可视化）
- FileList.vue - 通用文件列表组件
- ParseDetailsDrawer.vue - 解析详情抽屉

**UI/UX 增强 (2026-03-02)**:
- 队列管理三标签页（解析中/待解析/失败）
- 文档卡片网格布局
- 关键词搜索和状态筛选
- 详情抽屉展示完整信息
- 可视化统计卡片和分布条
- 单个文件操作按钮（解析/重试/移除）

**侧边栏优化 (2026-03-02)**:
- 移除标签页设计
- 底部添加永久"解析管理"按钮
- 点击跳转到独立页面
- 右键"添加到解析"保留

**技术修复 (2026-03-02)**:
- 统一字段命名为 `fileType`
- 计算属性兼容旧数据的 `type` 字段
- 修复单个文件解析报错问题
- 保持向后兼容性

### 相关文档

- [功能文档](./features/parse-management.md) (已更新)
- [实施报告](./implementation/2026-03-02-parse-management-refactor.md)
- [实施计划](./plans/2026-03-02-parse-management-refactor.md)

---

## 长期规划

### 性能优化

- 大文件分块渲染
- 图片懒加载
- 渲染缓存

### 安全增强

- API Key 加密存储
- CSP 策略优化
- 安全审计

### 用户体验

- 快捷键支持
- 拖拽操作
- 国际化

---

## 开发原则

- **奥卡姆剃刀**: 简单方案优先
- **KISS**: 保持简单
- **YAGNI**: 避免过度工程化
- **渐进式**: 小步迭代，快速交付
