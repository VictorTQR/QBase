# Markdown 文件添加到解析时没有实际索引 Bug 记录

**日期**: 2026-03-07  
**状态**: ✅ 已修复  
**严重程度**: 中

---

## 问题描述

将 Markdown 文件添加到解析时，会出现两个提示：
1. "已添加到解析队列"
2. "markdown文件无需解析可直接索引"

但是去解析管理中，既没有看到解析队列，也没有看到解析结果，也没有看到向量索引结果。

---

## 问题根因

### 问题 1: 没有实际执行索引操作

在 `app/src/stores/parse.js` 中的 `addFile` 函数（第 217-240 行），对于 Markdown 文件的处理是不完整的。

```javascript
} else if (fileType === 'markdown') {
  ElMessage.info('Markdown 文件无需解析，可直接索引向量')
  return { success: true, message: 'Markdown 文件无需解析' }
}
```

代码仅仅显示了一个提示信息，但**没有实际执行任何索引操作**！

### 问题 2: 没有正确处理 readMarkdown 的返回值

`window.electronAPI.readMarkdown()` 返回的是一个对象 `{success: true, content: "", frontmatter: {}}`，而不是直接返回字符串。需要从返回对象中提取 `content` 字段。

---

## 修复方案

修改 `app/src/stores/parse.js` 中的 `addFile` 函数，对于 Markdown 文件的情况：

1. 导入 `useVectorStore`
2. 使用 `window.electronAPI.readMarkdown` 读取文件内容
3. 从文件路径中提取文件名
4. 调用 `vectorStore.indexDocument` 来索引该文件

---

## 修复详情

### 任务 1: 导入 useVectorStore

**文件**: `app/src/stores/parse.js`

**修改内容**:
- 在文件顶部添加 `import { useVectorStore } from '@/stores/vector'`

---

### 任务 2: 修改 addFile 函数中 Markdown 文件的处理

**文件**: `app/src/stores/parse.js`

**修改内容**:
- 读取 Markdown 文件内容：`const result = await window.electronAPI.readMarkdown(filePath)`
- 检查读取结果：`if (!result.success) { throw new Error(...) }`
- 提取文件内容：`const content = result.content`
- 提取文件名：`const fileName = filePath.split(/[\\/]/).pop()`
- 调用向量索引：`await vectorStore.indexDocument(filePath, fileName, content)`
- 显示成功消息：`ElMessage.success('Markdown 文件已成功索引到向量库')`

---

## 修改文件清单

| 文件 | 修改类型 |
|------|---------|
| `app/src/stores/parse.js` | 添加 Markdown 文件索引逻辑 |

---

## 验证清单

- [x] useVectorStore 已导入
- [x] Markdown 文件读取逻辑已添加
- [x] 向量索引调用已添加
- [ ] Markdown 文件添加到解析后能正确索引到向量库
- [ ] 向量索引后能在搜索中找到该文件内容
