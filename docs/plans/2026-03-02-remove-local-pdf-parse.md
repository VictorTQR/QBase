# 移除本地 PDF 文本提取 - 实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 移除 QBase 中本地 PDF 文本提取功能，仅保留 MinerU 云端解析作为唯一的 PDF 文本提取方式。

**Architecture:** 保持 PdfViewer 组件的本地渲染功能不变（继续使用 pdfjs-dist），仅移除 TextExtractor 中的本地文本提取逻辑，简化为直接使用 MinerU 云端服务。

**Tech Stack:** JavaScript (ES6+), Pinia, Electron, MinerU API

---

## 背景与目标

当前 QBase 的 PDF 文本提取采用"本地优先，云端回退"的策略。本计划将其简化为**仅使用 MinerU 云端解析**，原因包括：
1. 本地 pdfjs-dist 文本提取质量有限，无法处理公式、表格等复杂元素
2. MinerU 提供更高级的 OCR、公式识别、表格解析能力
3. 简化代码维护，减少依赖冲突

**不包含在本次修改中：**
- PdfViewer 组件的 PDF 渲染功能（继续保留）
- pdfjs-dist 依赖（PdfViewer 仍需使用）

---

## 任务清单

### Task 1: 修改 TextExtractor.extractPdf() 方法

**Files:**
- Modify: `app/src/processors/parse/TextExtractor.js:35-52`

**Step 1: 读取当前 TextExtractor.js 文件**
使用 Read 工具读取完整文件，确认当前代码结构。

**Step 2: 简化 extractPdf() 方法**
将 `extractPdf()` 方法从"本地优先，云端回退"简化为"直接使用 MinerU"。

修改前：
```javascript
static async extractPdf(filePath, config = {}) {
  try {
    return await this.extractPdfLocal(filePath)
  } catch (localError) {
    console.warn('本地 PDF 提取失败，尝试云端 MinerU:', localError.message)

    if (config.mineru?.apiKey) {
      try {
        return await this.extractWithMinerU(filePath, config.mineru)
      } catch (mineruError) {
        console.error('MinerU 提取也失败:', mineruError)
        throw new Error(`PDF 提取失败: ${localError.message}`)
      }
    }

    throw new Error(`PDF 提取失败: ${localError.message}`)
  }
}
```

修改后：
```javascript
static async extractPdf(filePath, config = {}) {
  if (!config.mineru?.apiKey) {
    throw new Error('PDF 文本提取需要配置 MinerU API Key，请在设置中完成配置')
  }

  try {
    return await this.extractWithMinerU(filePath, config.mineru)
  } catch (error) {
    console.error('MinerU PDF 提取失败:', error)
    throw error
  }
}
```

**Step 3: 删除 extractPdfLocal() 方法**
删除 `TextExtractor.js` 中的 `extractPdfLocal()` 方法（第 54-87 行）。

**Step 4: 移除 pdfjs-dist 导入**
删除文件顶部的 pdfjs-dist 导入语句：
```javascript
import * as pdfjsLib from 'pdfjs-dist'
import pdfjsWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url'

pdfjsLib.GlobalWorkerOptions.workerSrc = pdfjsWorker
```

**Step 5: 验证文件语法**
检查修改后的文件是否有语法错误。

**Step 6: 提交变更**
```bash
cd app
git add src/processors/parse/TextExtractor.js
git commit -m "refactor: 移除本地 PDF 文本提取，仅使用 MinerU"
```

---

### Task 2: 验证修改（手动测试）

**Files:**
- 测试通过 UI 操作验证

**Step 1: 启动开发环境**
```bash
cd app
npm run dev
```
在另一个终端：
```bash
cd app
npm run ele
```

**Step 2: 测试无 MinerU 配置时的行为**
1. 确保未配置 MinerU API Key
2. 选择一个 PDF 文件
3. 尝试解析该 PDF
4. 验证是否显示友好的错误提示："PDF 文本提取需要配置 MinerU API Key，请在设置中完成配置"

**Step 3: 测试有 MinerU 配置时的行为**
1. 在设置中配置有效的 MinerU API Key
2. 选择一个 PDF 文件
3. 尝试解析该 PDF
4. 验证是否成功使用 MinerU 提取文本

**Step 4: 验证 PDF 查看功能不受影响**
1. 打开任意 PDF 文件
2. 验证 PdfViewer 组件能否正常渲染
3. 验证翻页、缩放等功能是否正常

---

## 回滚计划

如需回滚，执行以下操作：

```bash
cd app
git revert HEAD  # 撤销最新的提交
```

或者手动恢复 `TextExtractor.js` 到修改前的状态。

---

## 相关文件参考

| 文件 | 用途 |
|------|------|
| `app/src/processors/parse/TextExtractor.js` | 文本提取核心逻辑（本次修改的主要文件） |
| `app/src/components/PdfViewer.vue` | PDF 查看器（不受本次修改影响） |
| `app/src/stores/parse.js` | 解析状态管理 |
| `app/electron/main.js` | Electron 主进程（MinerU API 集成） |

---

## 后续可选优化

本次修改完成后，可考虑以下后续优化（不在本次计划范围内）：

1. **UI 提示优化**：在解析管理界面，当用户尝试解析 PDF 但未配置 MinerU 时，提供更明显的引导
2. **依赖清理**：评估是否可以拆分 pdfjs-dist，只保留 PdfViewer 需要的部分
3. **错误处理增强**：为 MinerU 解析失败提供更多恢复建议

---

## 验收标准

- [ ] `extractPdfLocal()` 方法已被删除
- [ ] pdfjs-dist 导入已从 TextExtractor.js 移除
- [ ] 无 MinerU 配置时，PDF 解析显示清晰的错误提示
- [ ] 有 MinerU 配置时，PDF 解析正常工作
- [ ] PdfViewer 组件的渲染功能不受影响
- [ ] 代码无语法错误
