# 导出功能与文本预览功能实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标：** 实现文档解析功能的文本预览和导出功能，包括单个文件导出和批量 ZIP 导出。

**架构：**
- 创建独立的 export 工具模块处理文件下载逻辑
- 在 ParseDetailsDrawer 中集成文本预览和单个导出
- 在 ParseManagement 中集成批量导出功能
- 使用已有的 jszip 库处理 ZIP 压缩

**技术栈：** Vue 3, Pinia, Element Plus, IndexedDB (Dexie), JSZip

---

## 任务 1：创建导出工具模块

**文件：**
- 创建：`app/src/utils/export.js`

### 步骤 1.1：创建 export.js 工具文件

```javascript
import JSZip from 'jszip'
import { ElMessage } from 'element-plus'

export function generateFileName(filePath) {
  const pathParts = filePath.split(/[/\\]/)
  const fullName = pathParts[pathParts.length - 1]
  const nameWithoutExt = fullName.replace(/\.[^/.]+$/, '')
  return `${nameWithoutExt}_extracted.txt`
}

export function exportSingleText(filePath, text, customFileName = null) {
  try {
    const fileName = customFileName || generateFileName(filePath)
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = fileName
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    return true
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败: ' + (error.message || '未知错误'))
    return false
  }
}

export async function exportAllTexts(fileMap) {
  try {
    const zip = new JSZip()
    let count = 0

    for (const [filePath, data] of Object.entries(fileMap)) {
      if (data && data.text) {
        const fileName = generateFileName(filePath)
        zip.file(fileName, data.text)
        count++
      }
    }

    if (count === 0) {
      ElMessage.warning('没有可导出的文本')
      return false
    }

    const content = await zip.generateAsync({ type: 'blob' })
    const url = URL.createObjectURL(content)
    const link = document.createElement('a')
    link.href = url
    link.download = `qbase_extracted_${Date.now()}.zip`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)

    ElMessage.success(`成功导出 ${count} 个文件`)
    return true
  } catch (error) {
    console.error('批量导出失败:', error)
    ElMessage.error('批量导出失败: ' + (error.message || '未知错误'))
    return false
  }
}
```

### 步骤 1.2：验证文件创建

检查文件是否在正确位置：`app/src/utils/export.js`

---

## 任务 2：增强 parse store - 批量获取文本

**文件：**
- 修改：`app/src/stores/parse.js`

### 步骤 2.1：在 parse.js 中添加新方法

在 `getExtractedText` 方法（第 221 行）之后添加：

```javascript
    async function getAllCompletedTexts() {
      const completedFiles = Object.entries(parseIndex.value)
        .filter(([, data]) => data.status === 'completed')
        .map(([filePath]) => filePath)

      const texts = {}
      for (const filePath of completedFiles) {
        const textData = await indexedDBRepo.getExtractedText(filePath)
        if (textData) {
          texts[filePath] = textData
        }
      }
      return texts
    }

    function getCompletedFiles() {
      return Object.entries(parseIndex.value)
        .filter(([, data]) => data.status === 'completed')
        .map(([filePath, data]) => ({ filePath, ...data }))
    }
```

### 步骤 2.2：在 return 中导出新方法

在 return 对象（第 247 行）中添加：

```javascript
      getAllCompletedTexts,
      getCompletedFiles,
```

位置：在 `getExtractedText,` 之后

---

## 任务 3：实现 ParseDetailsDrawer 文本预览

**文件：**
- 修改：`app/src/components/parse/ParseDetailsDrawer.vue`

### 步骤 3.1：修改 script 部分

在 `watch` 之后添加加载文本的逻辑：

```javascript
const loadingText = ref(false)
const fullText = ref(null)
const showFullPreview = ref(false)
const PREVIEW_LENGTH = 2000

watch(() => props.visible, async (val) => {
  if (!val) {
    emit('close')
    fullText.value = null
    showFullPreview.value = false
    return
  }
  if (val && props.filePath && fileData.value?.status === 'completed') {
    await loadExtractedText()
  }
})

async function loadExtractedText() {
  if (!props.filePath) return
  loadingText.value = true
  try {
    fullText.value = await parseStore.getExtractedText(props.filePath)
  } catch (error) {
    console.error('加载文本失败:', error)
    ElMessage.error('加载文本失败')
  } finally {
    loadingText.value = false
  }
}

const displayText = computed(() => {
  if (!fullText.value?.text) return null
  const text = fullText.value.text
  if (showFullPreview.value || text.length <= PREVIEW_LENGTH) {
    return text
  }
  return text.slice(0, PREVIEW_LENGTH) + '...'
})
```

### 步骤 3.2：修改模板部分

替换文本预览区域（第 31-36 行）：

```html
      <div v-if="fileData.status === 'completed'" class="detail-section">
        <h4>文本预览</h4>
        <div v-if="loadingText" class="text-preview loading">
          <el-icon class="is-loading"><Loading /></el-icon>
          加载中...
        </div>
        <div v-else-if="displayText" class="text-preview">
          {{ displayText }}
        </div>
        <div v-else class="text-preview empty">
          暂无文本内容
        </div>
        <div v-if="fullText?.text && fullText.text.length > PREVIEW_LENGTH" class="preview-toggle">
          <el-button link type="primary" size="small" @click="showFullPreview = !showFullPreview">
            {{ showFullPreview ? '收起' : '显示更多' }}
          </el-button>
        </div>
      </div>
```

### 步骤 3.3：添加必要的导入

在 script setup 顶部添加：

```javascript
import { Loading } from '@element-plus/icons-vue'
```

### 步骤 3.4：添加样式

在 style scoped 中添加：

```css
.text-preview.loading,
.text-preview.empty {
  color: var(--el-text-color-placeholder);
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 80px;
}

.text-preview.loading .el-icon {
  margin-right: 8px;
}

.preview-toggle {
  margin-top: 8px;
  text-align: center;
}
```

---

## 任务 4：实现 ParseDetailsDrawer 导出功能

**文件：**
- 修改：`app/src/components/parse/ParseDetailsDrawer.vue`

### 步骤 4.1：添加导出工具导入

在 script setup 顶部添加：

```javascript
import { exportSingleText } from '@/utils/export'
```

### 步骤 4.2：实现 handleExport 函数

替换 `handleExport` 函数（第 101-103 行）：

```javascript
async function handleExport() {
  if (!props.filePath || !fileData.value) return

  if (!fullText.value) {
    await loadExtractedText()
  }

  if (!fullText.value?.text) {
    ElMessage.warning('没有可导出的文本内容')
    return
  }

  const success = exportSingleText(props.filePath, fullText.value.text)
  if (success) {
    ElMessage.success('导出成功')
  }
}
```

---

## 任务 5：实现 ParseManagement 导出全部功能

**文件：**
- 修改：`app/src/views/ParseManagement.vue`

### 步骤 5.1：添加导入

在 script setup 顶部添加：

```javascript
import { exportAllTexts } from '@/utils/export'
```

### 步骤 5.2：添加状态和实现函数

在 `isParsing = ref(false)` 后添加：

```javascript
const exportingAll = ref(false)
```

替换 `handleExportAll` 函数（第 78-80 行）：

```javascript
async function handleExportAll() {
  const completed = parseStore.getCompletedFiles()
  if (completed.length === 0) {
    ElMessage.info('没有已完成解析的文件')
    return
  }

  exportingAll.value = true
  try {
    ElMessage.info('正在准备导出文件...')
    const allTexts = await parseStore.getAllCompletedTexts()
    await exportAllTexts(allTexts)
  } catch (error) {
    console.error('导出全部失败:', error)
    ElMessage.error('导出失败: ' + (error.message || '未知错误'))
  } finally {
    exportingAll.value = false
  }
}
```

### 步骤 5.3：更新模板按钮状态

修改"导出全部"按钮（第 12-14 行），添加 loading 状态：

```html
        <el-button size="small" @click="handleExportAll" :disabled="stats.completed === 0" :loading="exportingAll">
          导出全部
        </el-button>
```

---

## 测试步骤

### 测试 1：文本预览功能
1. 打开解析管理页面
2. 点击一个已完成解析的文件
3. 验证文本预览区域显示内容
4. 如果文本很长，验证"显示更多"按钮功能

### 测试 2：单个文件导出
1. 在详情抽屉中点击"导出文本"
2. 验证文件下载成功
3. 验证文件名和内容正确

### 测试 3：批量导出
1. 确保有多个已完成解析的文件
2. 点击"导出全部"按钮
3. 验证 ZIP 文件下载成功
4. 解压验证内容完整性

---

## 检查清单

- [ ] `app/src/utils/export.js` 已创建
- [ ] parse store 新增方法已添加
- [ ] ParseDetailsDrawer 文本预览功能正常
- [ ] ParseDetailsDrawer 单个导出功能正常
- [ ] ParseManagement 批量导出功能正常
- [ ] 所有测试步骤验证通过
