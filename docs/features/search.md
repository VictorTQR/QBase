# 搜索增强功能

**状态**: ✅ 已完成
**版本**: v1.0
**完成日期**: 2026-03-03

## 功能概述

搜索增强功能提供了强大的全文搜索和向量搜索能力，支持搜索所有工作区中的文件，包括基于语义的向量搜索。

## 功能特性

### 1. 搜索面板
- 独立的弹出式搜索面板
- 支持快捷键 `Ctrl/Cmd + K` 快速打开
- 美观的 UI，带有搜索结果高亮

### 2. 搜索能力
- 支持文件名搜索
- 支持文件内容搜索
- 支持 YAML frontmatter 搜索（title, date, author, tags, description 等）
- 显示匹配内容的上下文片段
- 大小写不敏感匹配
- 自动防抖搜索（300ms）

### 3. 搜索范围
- 可选择搜索所有工作区
- 可选择搜索特定文件夹
- 记住用户上次选择的搜索范围

### 4. 搜索模式
- **全文搜索**：传统的关键词匹配搜索
- **向量搜索**：基于语义的向量相似性搜索
- **混合搜索**：结合全文和向量搜索的结果
- 记住用户上次选择的搜索模式

### 5. 搜索结果展示
- 文件名高亮显示搜索关键词
- 显示匹配类型标签（文件名/内容/向量）
- 显示内容片段预览
- 显示相似度分数（向量搜索）
- 显示完整文件路径
- 支持键盘导航

### 6. 快捷键支持
| 快捷键 | 功能 |
|---------|------|
| `Ctrl/Cmd + K` | 打开搜索面板 |
| `↑` / `↓` | 导航搜索结果 |
| `Enter` | 打开选中的文件 |
| `Esc` | 关闭搜索面板 |

## 技术实现

### 数据结构

**搜索结果项**:
```javascript
{
  id: string,           // 文件完整路径
  name: string,         // 文件名
  path: string,         // 文件路径
  type: 'file',
  matchType: 'name' | 'content' | 'vector',  // 匹配类型
  snippet: string,      // 匹配内容的上下文片段
  score?: number,       // 相似度分数（向量搜索）
  chunkIndex?: number,  // 分块索引（向量搜索）
}
```

### 向量搜索数据结构

**向量搜索结果**:
```javascript
{
  id: string,           // 分块 ID
  file_path: string,    // 文件完整路径
  file_name: string,    // 文件名
  workspace_id: string, // 工作区 ID
  chunk_index: number,  // 分块索引
  content: string,      // 分块内容
  score: number,        // 相似度分数 (0-1)
}
```

### 目录结构

```
app/
├── electron/
│   └── main.js              # 搜索 IPC 处理器（增强）
└── src/
    ├── api/
    │   └── vectorBackend.js  # 向量搜索后端 API 客户端（新建）
    ├── stores/
    │   ├── search.js         # 搜索状态管理（增强）
    │   └── vector.js         # 向量搜索状态管理（新建）
    └── components/
        ├── SearchPanel.vue    # 搜索面板（增强）
        └── Layout/
            └── MainLayout.vue  # 集成搜索按钮
```

### Store 设计

**Search Store (`app/src/stores/search.js`):

- `query`: 搜索关键词
- `results`: 搜索结果列表
- `isLoading`: 搜索加载状态
- `isPanelOpen`: 搜索面板显示状态
- `searchScope`: 搜索范围
- `searchMode`: 搜索模式 ('fulltext' | 'vector' | 'hybrid')
- `selectedIndex`: 选中结果索引

**主要方法**:
- `openPanel()`: 打开搜索面板
- `closePanel()`: 关闭搜索面板
- `performSearch()`: 执行搜索
- `performFulltextSearch()`: 执行全文搜索
- `performVectorSearch()`: 执行向量搜索
- `performHybridSearch()`: 执行混合搜索
- `setSearchMode()`: 设置搜索模式
- `selectPreviousResult()`: 选择上一个结果
- `selectNextResult()`: 选择下一个结果
- `getSelectedResult()`: 获取当前选中的结果

**Vector Store (`app/src/stores/vector.js`):

- `isIndexing`: 是否正在索引
- `indexingProgress`: 索引进度
- `indexingTotal`: 索引总数
- `currentIndexingFile`: 当前索引文件
- `error`: 错误信息
- `stats`: 统计信息

**主要方法**:
- `indexDocument()`: 索引文档
- `searchVectors()`: 搜索向量
- `deleteDocumentChunks()`: 删除文档分块
- `loadStats()`: 加载统计信息
- `clearAll()`: 清空所有向量数据

### 后端增强

**Electron IPC (`app/electron/main.js`):

- `search-files`: 搜索文件
  - 参数：folderPath, query
  - 返回：成功状态和结果列表
  - 增强：返回 matchType 和 snippet

**向量搜索后端 API**:

- `POST /api/vector/index`: 索引文档
- `POST /api/vector/search`: 向量搜索
- `DELETE /api/vector/delete`: 删除文档分块
- `GET /api/vector/stats`: 获取统计信息
- `POST /api/vector/clear`: 清空所有向量数据

### 搜索算法

#### 全文搜索算法
1. 递归遍历文件夹
2. 匹配文件名（优先）
3. 读取文件内容
4. 提取匹配位置前后各 50 字符作为片段
5. 返回匹配结果

#### 向量搜索算法
1. 将查询文本转换为向量嵌入
2. 在 LanceDB 中进行相似度搜索
3. 返回最相似的文档分块
4. 按文件合并结果
5. 返回搜索结果

#### 混合搜索算法
1. 并行执行全文搜索和向量搜索
2. 合并两种搜索的结果
3. 对重叠结果进行分数加权
4. 按综合分数排序
5. 返回最终结果

## 使用流程

### 搜索流程

```
用户输入关键词
    ↓
防抖延迟 (300ms)
    ↓
根据搜索模式选择
    ↓
┌─────────────────────────────────────┐
│  全文搜索       │  向量搜索      │  混合搜索
│                  │                 │
│  Electron IPC    │  向量 API       │  并行执行
│  文件名/内容匹配 │  语义相似度      │  结果合并
│  片段提取         │  分块搜索        │  分数加权
└─────────────────────────────────────┘
    ↓
返回搜索结果
    ↓
前端渲染结果列表
    ↓
高亮匹配关键词
    ↓
显示相似度分数（向量搜索）
    ↓
用户选择结果
    ↓
打开对应文件
```

## UI 展示

### 搜索面板布局

```
┌─────────────────────────────────┐
│  [搜索输入框              │
├─────────────────────────────────┤
│  搜索范围: [所有工作区 ▼   │
├─────────────────────────────────┤
│  [全文] [向量] [混合]      │
├─────────────────────────────────┤
│  📄 文件名.md [向量] [85%] │
│     向量搜索匹配内容...         │
│     /完整/文件/路径           │
│                             │
│  📄 文件名.md [内容]      │
│     全文搜索匹配内容...        │
│     /完整/文件/路径       │
├─────────────────────────────────┤
│  ↑↓ 导航  Enter 打开  Esc 关闭 │
└─────────────────────────────────┘
```

## 后续扩展

- 搜索历史记录
- 高级搜索选项（正则表达式、大小写敏感）
- 搜索结果排序选项
- 实时搜索索引缓存
- 搜索结果内打开新标签页

## 更新记录

### 2026-03-03 - 向量搜索功能
- 新增向量搜索模式，基于 LanceDB 后端实现
- 新增混合搜索模式，结合全文和向量搜索
- 创建 vectorBackend.js API 客户端
- 创建 vector.js Pinia store
- 增强 SearchPanel，添加搜索模式切换
- 更新 useSearchStore，支持多种搜索模式
- 显示相似度分数（向量搜索）
- 持久化用户搜索模式选择

### 2026-02-27 - YAML Frontmatter 搜索集成
- 搜索内容包含 Markdown 文档的 YAML frontmatter
- frontmatter 的所有字段值都参与搜索匹配
- 使用 gray-matter 在 Electron 主进程解析 frontmatter
- 相关 bug 记录：[XMarkdown CSP 修复](../bugs/2026-02-27-xmarkdown-csp-wasm-eval.md)
