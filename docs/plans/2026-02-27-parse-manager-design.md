# 文档解析管理功能设计方案

## 概述

本文档描述 QBase 文档解析管理功能的设计方案，包括文本提取、音视频转录、向量化表示的统一管理界面。

## 状态标记：✅ 已完成

## 目标

为用户需求：

- 提供统一的解析状态监控
- 管理解析任务（待解析、解析中、已完成、失败）
- 查看解析详情（提取文本、转录内容、向量信息）
- 支持批量操作

## 方案设计

### 布局设计

左侧区域改造为双标签切换设计：

```
┌─────────────────────────────────┐
│  📁 文件树  │  ⚙️ 解析管理   │ ← 顶部横向标签（el-tabs）
├─────────────────────────────────┤
│                                 │
│   内容区域（根据标签切换）       │
│                                 │
└─────────────────────────────────┘
```

- 默认选中「文件树」标签，保持现有体验不变
- 点击「解析管理」切换到解析管理界面

### 解析管理界面结构：

```
┌─────────────────────────────────────────────────────┐
│  📊 统计概览区域                            │
│  已解析: 42/100  |  解析中: 3  |  失败: 2         │
│  [批量解析全部]  [重新解析失败]                     │
├──────────────────────┬──────────────────────────────┤
│  📋 解析队列        │  📁 文档列表                 │
│  • 待解析 (5)       │  [文件夹树结构]              │
│  • 解析中 (3)       │  📂 工作区/                  │
│  • 失败 (2)         │    📄 doc1.md [✅]          │
│                     │    📄 video.mp4 [⏳]         │
│                     │    📄 doc2.pdf [❌]         │
├──────────────────────┴──────────────────────────────┤
│  📄 解析详情面板（点击文档时展开）                  │
│  文件: doc1.md                                       │
│  状态: 已完成 | 耗时: 2.3s | 大小: 15KB            │
│  [查看提取文本]  [查看向量数据]  [重新解析]        │
└─────────────────────────────────────────────────────┘
```

## 技术方案

### 数据存储方案：混合方案

- **LocalStorage（Pinia 持久化**：存储解析索引（轻量元数据）
- **IndexedDB（Dexie.js）**：存储大文本、向量数据

### Dexie.js 数据库设计

```javascript
import Dexie from 'dexie'

const db = new Dexie('QBaseParse')
db.version(1).stores({
  extractedTexts: 'filePath, type, parsedAt',
  vectors: 'filePath',
  transcripts: 'filePath'
})
```

### Store 设计

**Store：`useParseStore`

```javascript
{
  // 解析索引（LocalStorage 持久化）
  parseIndex: {
    'file-path-1': {
      status: 'completed',      // pending | parsing | completed | failed
      parsedAt: 1234567890,
      duration: 2300,
      size: 15360,
      type: 'markdown',
      error: null
    }
  },

  // 当前解析队列
  queue: [],

  // 当前活动的解析任务
  activeTask: null,

  // UI 状态
  selectedFile: null,
  showDetails: false
}
```

## 实现计划

### 文件结构变更

```
app/src/
├── components/
│   ├── Layout/
│   │   ├── Sidebar.vue              (修改: 添加标签切换)
│   │   ├── ParseManager.vue         (新增: 解析管理主组件)
│   │   ├── ParseStats.vue           (新增: 统计概览)
│   │   ├── ParseQueue.vue           (新增: 解析队列)
│   │   ├── ParseDocumentList.vue    (新增: 文档列表)
│   │   └── ParseDetails.vue         (新增: 解析详情)
├── stores/
│   └── parse.js                      (新增: 解析管理 Store)
├── repositories/
│   ├── ParseIndexRepository.js      (新增: 解析索引仓储)
│   └── IndexedDBRepository.js       (新增: IndexedDB 封装)
└── processors/
    └── parse/                        (新增: 解析处理器目录)
        ├── TextExtractor.js
        ├── AudioTranscriber.js
        └── Vectorizer.js
```

## 风险与依赖

| 风险/依赖 | 应对措施 |
|------------|---------|
| Dexie.js 依赖 | 需要安装 `dexie` 包 |
| IndexedDB 容量限制 | Electron 环境下通常有足够空间 |
| 解析性能 | 初期仅实现状态管理，具体解析逻辑后续迭代 |

## 后续优化方向

- 实际的文本提取实现
- 音视频转录集成
- 向量化表示功能

## 备注

- 设计日期：2026-02-27
