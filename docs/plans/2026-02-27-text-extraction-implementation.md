# 文本提取功能实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标:** 实现 Markdown 和 PDF 的文本提取功能，集成到解析管理工作流中

**架构:** 采用混合策略，优先使用本地提取（pdfjs-dist），可选云端 MinerU 增强；使用 IndexedDB 存储提取结果，LocalStorage 存储解析索引

**技术栈:** Vue 3, Pinia, Dexie.js, pdfjs-dist, Element Plus

---

## 阶段 1：Markdown 文本提取

### Task 1.1: 实现 MarkdownExtractor

**文件:**
- 修改: `app/src/processors/parse/TextExtractor.js`

**步骤:**

1. 扩展 TextExtractor 类，添加 extractMarkdown 方法
2. 使用 window.electronAPI.readMarkdown() 读取文件
3. 提取正文内容（去除 frontmatter）
4. 返回结构化的提取结果

---

## 阶段 2：本地 PDF 文本提取

### Task 2.1: 实现 PdfExtractor（基于 pdfjs-dist）

**文件:**
- 修改: `app/src/processors/parse/TextExtractor.js`
- 参考: `app/src/components/PdfViewer.vue`

**步骤:**

1. 添加 extractPdf 静态方法
2. 使用 pdfjs-dist 加载 PDF 文件
3. 逐页提取文本并拼接
4. 添加页码标注
5. 返回结构化结果（含页数、字数等元数据）

---

## 阶段 3：TextExtractor 统一入口

### Task 3.1: 实现主 extract 方法

**文件:**
- 修改: `app/src/processors/parse/TextExtractor.js`

**步骤:**

1. 实现静态 extract(filePath, fileType, config) 方法
2. 根据文件类型路由到相应的提取器
3. 实现智能选择逻辑：优先本地，失败时尝试云端（如果配置）
4. 统一返回格式

---

## 阶段 4：ParseStore 扩展

### Task 4.1: 扩展 useParseStore

**文件:**
- 修改: `app/src/stores/parse.js`

**步骤:**

1. 添加 startParse(filePath) 方法
2. 添加 startParseBatch(filePaths) 方法
3. 添加 updateParseStatus(filePath, status, result) 方法
4. 集成 TextExtractor
5. 集成 IndexedDBRepository 保存结果

---

## 阶段 5：UI 集成

### Task 5.1: 集成到 ParseManager

**文件:**
- 修改: `app/src/components/Layout/ParseManager.vue`
- 修改: `app/src/components/Layout/ParseDetails.vue`

**步骤:**

1. 连接"解析"按钮到 startParse()
2. 连接"批量解析"按钮到 startParseBatch()
3. 在 ParseDetails 中显示提取的文本预览
4. 添加加载状态和错误提示

---

## 验收标准

- [ ] Markdown 文件可以成功提取文本
- [ ] PDF 文件可以成功提取文本（本地）
- [ ] 解析状态正确更新
- [ ] 提取结果保存到 IndexedDB
- [ ] UI 可以显示解析进度和结果
- [ ] 错误处理友好

---

## 后续增强（可选）

- MinerU 云端提取集成
- 更多文件格式支持（.docx, .pptx 等）
- OCR 功能
- 批量解析优化
