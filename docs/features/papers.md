# 论文管理功能

**状态**: ✅ 已完成
**版本**: v1.1
**完成日期**: 2026-04-05

## 功能概述

论文管理功能提供了与 arXiv 论文库的集成，支持搜索、保存和管理学术论文。用户可以通过关键词搜索相关论文，并将感兴趣的论文保存到本地数据库中，方便后续查看和管理。

## 功能特性

### 1. arXiv 论文搜索
- 支持关键词搜索 arXiv 论文库
- 多种排序方式：相关性、最后更新日期、提交日期
- 可调整搜索结果数量（1-100篇）
- 实时显示搜索结果
- 显示论文标题、作者、摘要等信息

### 2. 论文保存和管理
- 一键保存搜索结果到本地数据库
- 支持批量保存多篇论文
- 自动去重，避免重复保存
- 保存完整的论文元数据

### 3. 论文统计信息
- 论文总数统计
- 作者总数统计
- 分类总数统计
- 最新论文日期追踪

### 4. 论文列表展示
- 分页展示已保存的论文
- 显示论文标题、作者、arXiv ID、发布日期、分类
- 支持按分页大小查看（10/20/50/100篇）
- 表格形式展示，清晰直观

### 5. 论文详情查看
- 查看完整论文信息
- 显示论文摘要
- 显示所有分类标签
- 支持跳转到 arXiv 页面
- 支持直接打开 PDF

### 6. 快速访问
- 直接在应用内打开 PDF 文件
- 快速跳转到 arXiv 论文页面
- 在浏览器中打开完整论文信息

## 技术实现

### 前端架构

#### 目录结构

```
app/src/
├── views/
│   └── PapersView.vue           # 论文管理主页面
├── components/
│   ├── PaperList.vue            # 论文列表组件
│   └── PaperSearchDialog.vue    # 搜索对话框组件
├── api/
│   └── papers.js                # 论文 API 客户端
└── router/
    └── index.js                 # 路由配置
```

#### 数据结构

**论文对象**:
```javascript
{
  id: string,              // 数据库 ID
  arxiv_id: string,        // arXiv ID（如：2301.12345）
  title: string,           // 论文标题
  authors: string[],       // 作者列表
  summary: string,         // 摘要
  published_date: string,  // 发布日期（ISO 8601）
  primary_category: string, // 主分类
  categories: string[],    // 所有分类
  created_at: string       // 保存时间
}
```

**统计信息**:
```javascript
{
  total_papers: number,        // 论文总数
  total_authors: number,       // 作者总数
  total_categories: number,    // 分类总数
  latest_paper_date: string    // 最新论文日期
}
```

#### 组件设计

**PapersView（主页面）**:
- 展示统计信息卡片
- 提供搜索入口
- 集成论文列表
- 提供刷新功能

**PaperList（列表组件）**:
- 表格形式展示论文
- 支持分页
- 提供详情查看
- 提供 PDF 和 arXiv 链接

**PaperSearchDialog（搜索对话框）**:
- 搜索表单（关键词、排序、数量）
- 搜索结果展示
- 批量保存功能
- 单篇论文快速访问

#### API 客户端

**PapersBackendApi 类** (`app/src/api/papers.js`):

```javascript
export class PapersBackendApi {
  // 搜索 arXiv 论文
  static async searchPapers(keyword, maxResults = 10, sortBy = 'relevance')

  // 保存搜索结果到数据库
  static async savePapers(keyword, maxResults = 10, sortBy = 'relevance')

  // 获取已保存的论文列表
  static async getPaperList(offset = 0, limit = 50)

  // 获取论文统计信息
  static async getPaperStats()
}
```

### 后端实现

#### API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/papers/search` | POST | 搜索 arXiv 论文 |
| `/api/papers/save` | POST | 保存论文到数据库 |
| `/api/papers/list` | GET | 获取论文列表 |
| `/api/papers/stats` | GET | 获取统计信息 |

#### 请求格式

**搜索论文**:
```json
POST /api/papers/search
{
  "keyword": "machine learning",
  "max_results": 10,
  "sort_by": "relevance"
}
```

**保存论文**:
```json
POST /api/papers/save
{
  "keyword": "machine learning",
  "max_results": 10,
  "sort_by": "relevance"
}
```

**获取列表**:
```
GET /api/papers/list?offset=0&limit=50
```

#### 响应格式

**成功响应**:
```json
{
  "success": true,
  "data": {
    "papers": [...],
    "total": 100
  }
}
```

**错误响应**:
```json
{
  "success": false,
  "message": "错误描述"
}
```

#### 数据库设计

**papers 表**:
```sql
CREATE TABLE papers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  arxiv_id TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  authors TEXT NOT NULL,  -- JSON 数组字符串
  summary TEXT,
  published_date TEXT,
  primary_category TEXT,
  categories TEXT,  -- JSON 数组字符串
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**索引**:
- `arxiv_id`: 唯一索引，防止重复
- `published_date`: 用于排序和统计
- `primary_category`: 用于分类统计

## 使用流程

### 搜索和保存论文

```
用户打开论文管理页面
    ↓
点击"搜索论文"按钮
    ↓
打开搜索对话框
    ↓
输入关键词，选择排序方式和结果数量
    ↓
点击"搜索"按钮
    ↓
后端调用 arXiv API 搜索论文
    ↓
前端显示搜索结果
    ↓
用户查看结果，可选择：
  - 查看 PDF（在浏览器打开）
  - 访问 arXiv 页面
  - 保存全部到数据库
    ↓
点击"保存全部"
    ↓
后端保存论文到数据库（自动去重）
    ↓
显示保存成功提示
    ↓
论文列表自动刷新
```

### 查看已保存论文

```
用户打开论文管理页面
    ↓
查看统计信息（总数、作者、分类、最新日期）
    ↓
浏览论文列表
    ↓
可进行以下操作：
  - 查看详情（打开详情对话框）
  - 打开 PDF（在浏览器打开）
  - 访问 arXiv 页面
  - 切换分页
  - 调整每页显示数量
    ↓
点击"详情"按钮
    ↓
打开详情对话框
    ↓
查看完整论文信息
  - 标题、作者、日期
  - 完整摘要
  - 所有分类标签
  - 快速访问链接
```

## UI 展示

### 论文管理页面布局

```
┌─────────────────────────────────────────────────────┐
│  [←] 论文管理                        [刷新]        │
├─────────────────────────────────────────────────────┤
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐                  │
│  │ 100 │ │ 256 │ │  45 │ │2024-│  统计卡片        │
│  │论文 │ │作者 │ │分类 │ │04-01│                  │
│  └─────┘ └─────┘ └─────┘ └─────┘                  │
├─────────────────────────────────────────────────────┤
│  [搜索论文]                                         │
├─────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────┐  │
│  │ 论文列表（表格形式）                          │  │
│  │                                               │  │
│  │ 标题 | arXiv ID | 日期 | 分类 | 操作          │  │
│  │ ───────────────────────────────────────────  │  │
│  │ Paper Title...        [PDF] [arXiv] [详情]  │  │
│  │ Another Paper...      [PDF] [arXiv] [详情]  │  │
│  │ ...                                           │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  [分页控件]                                         │
└─────────────────────────────────────────────────────┘
```

### 搜索对话框布局

```
┌──────────────────────────────────────────┐
│  搜索 arXiv 论文                          │
├──────────────────────────────────────────┤
│  搜索关键词: [__________________]        │
│  排序方式:   [相关性 ▼]                   │
│  结果数量:   [10          ]               │
│                                           │
│  [搜索] [重置]                            │
├──────────────────────────────────────────┤
│  找到 10 篇论文          [保存全部]       │
│  ─────────────────────────────────────   │
│  ┌────────────────────────────────────┐ │
│  │ Paper Title...                     │ │
│  │ 作者: Author1, Author2             │ │
│  │ 摘要: This is a summary...         │ │
│  │ arXiv ID | 2024-04-01 | [CS.AI]   │ │
│  │ [查看 PDF] [arXiv 页面]            │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │ Another Paper...                   │ │
│  │ ...                                │ │
│  └────────────────────────────────────┘ │
└──────────────────────────────────────────┘
```

## 排序方式说明

| 排序方式 | 说明 | 适用场景 |
|---------|------|---------|
| relevance | 相关性排序（默认） | 查找与关键词最相关的论文 |
| lastUpdatedDate | 最后更新日期 | 查找最近更新的论文 |
| submittedDate | 提交日期 | 查找最新提交的论文 |

## 后续扩展

- [ ] 论文标签管理
- [ ] 论文收藏夹
- [ ] 论文笔记功能
- [ ] 论文推荐（基于已保存论文）
- [ ] 批量导出论文信息
- [ ] 论文全文搜索
- [ ] 与 AI 助手集成，提供论文问答

## 相关文档

- [后端 API 文档](../api/papers-api.md)
- [数据库设计](../architecture/database.md)
- [arXiv API 文档](https://arxiv.org/help/api)

## 更新记录

### 2026-04-05 - 论文管理功能
- 新增 arXiv 论文搜索功能
- 新增论文保存到本地数据库
- 新增论文列表展示和分页
- 新增论文统计信息
- 新增论文详情查看
- 新增快速访问 PDF 和 arXiv 页面
- 创建 PapersBackendApi API 客户端
- 创建 PapersView 主页面
- 创建 PaperList 列表组件
- 创建 PaperSearchDialog 搜索对话框
