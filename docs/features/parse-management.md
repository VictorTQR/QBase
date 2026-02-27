# 文档解析管理

**状态**: 🔄 进行中

## 概述

文档解析管理功能提供了一个统一的界面来管理文档的文本提取、音视频转录、向量化表示等任务。

## 功能特性

### 双标签页布局

左侧区域采用横向标签页设计，支持在「文件树」和「解析管理」之间切换：

```
┌─────────────────────────────────┐
│  📁 文件树  │  ⚙️ 解析管理   │
├─────────────────────────────────┤
│                                 │
│   内容区域（根据标签切换）       │
│                                 │
└─────────────────────────────────┘
```

### 解析管理界面

解析管理界面包含以下模块：

1. **统计概览**
   - 显示总计、已完成、待解析、解析中、失败的文档数量
   - 提供「批量解析」和「重试失败」按钮

2. **解析队列**
   - 解析中任务展示
   - 待解析任务列表
   - 失败任务展示（含错误信息）

3. **文档列表**
   - 文件夹树形式展示所有文档
   - 每个文档带状态图标（✅/⏳/🔄/❌）
   - 显示解析耗时、大小等元信息

4. **解析详情**
   - 选择文档后展开详情面板
   - 查看解析状态、类型、耗时、大小
   - 支持「重新解析」和「删除记录」操作

## 技术实现

### 混合存储方案

- **LocalStorage（Pinia 持久化）**：存储解析索引（轻量元数据）
  - 文件路径 → 状态、时间戳、类型等
  - 使用 `useParseStore` 管理

- **IndexedDB（Dexie.js）**：存储大文本、向量数据
  - `extractedTexts` - 提取的文本内容
  - `vectors` - 向量化数据
  - `transcripts` - 音视频转录结果

### 文件结构

```
app/src/
├── components/Layout/
│   ├── ParseManager.vue       # 解析管理主组件
│   ├── ParseStats.vue         # 统计概览
│   ├── ParseQueue.vue         # 解析队列
│   ├── ParseDocumentList.vue  # 文档列表
│   └── ParseDetails.vue       # 解析详情
├── stores/
│   └── parse.js               # useParseStore
├── repositories/
│   ├── IndexedDBRepository.js # Dexie.js 封装
│   └── ParseIndexRepository.js # LocalStorage 存储
└── processors/parse/
    ├── TextExtractor.js       # 文本提取器（占位）
    ├── AudioTranscriber.js    # 音频转录器（占位）
    └── Vectorizer.js          # 向量化器（占位）
```

### Store 设计

**useParseStore** 提供以下功能：

```javascript
{
  // 状态
  parseIndex,      // 解析索引
  queue,           // 解析队列
  activeTask,      // 当前活动任务
  selectedFile,    // 选中的文件
  showDetails,     // 是否显示详情
  
  // 计算属性
  stats,           // 统计数据
  pendingFiles,    // 待解析文件
  parsingFiles,    // 解析中文件
  failedFiles,     // 失败文件
  
  // 方法
  loadIndex(),     // 加载索引
  addFile(),       // 添加文件
  startParsing(),  // 开始解析
  completeParsing(), // 完成解析
  failParsing(),   // 解析失败
  retryFailed(),   // 重试失败
  reparse(),       // 重新解析
  selectFile(),    // 选择文件
  closeDetails()   // 关闭详情
}
```

## 后续规划

### 待实现功能

- [ ] 真实的文本提取实现
- [ ] 音视频转录集成
- [ ] 向量化表示功能
- [ ] 批量解析调度
- [ ] 解析进度显示

### 相关文档

- [设计文档](../plans/2026-02-27-parse-manager-design.md)
- [实施计划](../plans/2026-02-27-parse-manager-implementation.md)
