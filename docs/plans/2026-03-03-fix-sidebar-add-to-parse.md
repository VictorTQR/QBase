# 修复 Sidebar 右键"添加到解析"功能 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 修复 Sidebar.vue 中右键菜单"添加到解析"功能报错的问题。

**Architecture:** 在 parseStore 中添加 addFile() 方法，根据文件类型分发到相应的解析处理（PDF/音频）。

**Tech Stack:** Vue 3 + Pinia

---

## Task 1: 在 parseStore 中添加 addFile() 方法

**Files:**
- Modify: `app/src/stores/parse.js`

**Step 1: 添加 addFile 方法**

在 `parse.js` 的 return 语句之前添加：

```javascript
async function addFile(filePath, fileType) {
  isLoading.value = true
  error.value = null
  try {
    if (fileType === 'pdf') {
      return await parseLocalFile(filePath)
    } else if (fileType === 'audio') {
      const { useAudioStore } = await import('@/stores/audio')
      const audioStore = useAudioStore()
      const { useParseConfigStore } = await import('@/stores/parseConfig')
      const parseConfigStore = useParseConfigStore()
      const { asrModel } = parseConfigStore.audioConfig
      return await audioStore.transcribeLocalFile(filePath, asrModel)
    } else if (fileType === 'markdown') {
      ElMessage.info('Markdown 文件无需解析，可直接索引向量')
      return { success: true, message: 'Markdown 文件无需解析' }
    } else {
      throw new Error(`不支持的文件类型: ${fileType}`)
    }
  } catch (err) {
    error.value = err.message
    throw err
  } finally {
    isLoading.value = false
  }
}
```

**Step 2: 导入 ElMessage**

在文件顶部添加：
```javascript
import { ElMessage } from 'element-plus'
```

**Step 3: 在 return 中导出 addFile**

```javascript
return {
  // ... 现有导出
  addFile,
}
```

**Step 4: Commit**

```bash
cd app
git add src/stores/parse.js
git commit -m "fix: 在parseStore中添加addFile方法"
```

---

## 执行总结

### 完成标准
- [ ] Task 1: addFile() 方法已添加到 parseStore
- [ ] 右键"添加到解析"功能正常工作

---

**Plan complete and saved to `docs/plans/2026-03-03-fix-sidebar-add-to-parse.md`.**
