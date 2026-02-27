# 文本提取功能设计文档

**创建日期**: 2026-02-27  
**状态**: ✅ 已确认  
**版本**: v0.7

---

## 一、设计概述

### 1.1 决策总结

| 维度 | 选择 |
|------|------|
| **文件格式** | Markdown + PDF（基础组合）|
| **实现策略** | 混合策略（本地 pdfjs-dist + 云端 MinerU）|
| **触发方式** | 手动触发 + 批量解析 |
| **存储策略** | 完整可用（IndexedDB 存储，多功能复用）|

### 1.2 设计原则

- **KISS**: 保持简单，优先实现核心功能
- **渐进式**: 分阶段迭代，快速验证
- **B+ 架构**: 接口统一，实现可替换

---

## 二、架构设计

### 2.1 TextExtractor 分层架构

```
TextExtractor (统一入口)
    ↓
    ├─ MarkdownExtractor (本地)
    ├─ PdfExtractor (本地，基于 pdfjs-dist)
    └─ MinerUExtractor (云端，基于 MinerU API)
```

### 2.2 核心流程

```
用户点击解析
    ↓
TextExtractor.extract(filePath, fileType)
    ↓
判断文件类型
    ↓
Markdown/PDF: 优先本地提取 → 失败则尝试云端（如果配置）
    ↓
保存到 IndexedDB (IndexedDBRepository)
    ↓
更新解析索引 (ParseIndexRepository)
    ↓
更新 UI 状态 (useParseStore)
```

---

## 三、核心组件设计

### 3.1 TextExtractor 主类

**文件位置**: `app/src/processors/parse/TextExtractor.js`

**职责**: 统一入口，路由到具体的提取器实现

**核心方法**:
```javascript
class TextExtractor {
  static async extract(filePath, fileType)
  static async extractMarkdown(filePath)
  static async extractPdf(filePath, config)
  static async extractWithMinerU(filePath, config)
}
```

### 3.2 本地提取器

#### MarkdownExtractor
- 使用现有的 `readMarkdown()` API
- 提取正文内容（去除 frontmatter）

#### PdfExtractor
- 基于 pdfjs-dist 实现
- 逐页提取文本并拼接
- 支持页码标注

### 3.3 云端提取器（MinerUExtractor）
- 复用现有的 MinerUProcessor
- 仅在用户配置了 MinerU API Key 时使用
- 提供更强大的解析能力（OCR、结构化）

---

## 四、集成到解析管理工作流

### 4.1 ParseStore 扩展

新增方法:
- `startParse(filePath)` - 开始解析单个文件
- `startParseBatch(filePaths)` - 批量解析
- `updateParseStatus(filePath, status, result)` - 更新解析状态

### 4.2 ParseManager UI 集成
- 连接"解析"按钮到 `startParse()`
- 连接"批量解析"按钮到 `startParseBatch()`
- 显示解析进度和结果

---

## 五、数据存储设计

### 5.1 IndexedDB 存储结构

```javascript
// extractedTexts 表
{
  filePath: String (primary key),
  text: String,
  fileType: String,
  extractedBy: 'local' | 'mineru',
  extractedAt: Date,
  pageCount?: Number,  // PDF 专用
  wordCount?: Number
}
```

### 5.2 解析索引结构（LocalStorage）

```javascript
{
  [filePath]: {
    status: 'pending' | 'parsing' | 'completed' | 'failed',
    fileType: String,
    startedAt?: Date,
    completedAt?: Date,
    error?: String,
    extractedBy?: 'local' | 'mineru'
  }
}
```

---

## 六、错误处理

1. **本地提取失败** → 记录日志，标记为失败
2. **云端提取失败** → 降级到本地提取（如果适用）
3. **文件不存在** → 友好提示用户
4. **格式不支持** → 明确提示支持的格式

---

## 七、实现优先级

### Phase 1（核心）
- Markdown 文本提取
- 本地 PDF 文本提取（pdfjs-dist）
- 集成到解析管理 UI

### Phase 2（增强）
- MinerU 云端提取集成
- 批量解析功能
- 解析结果预览

---

**文档状态**: ✅ 已确认，等待实施
