# Bug 修复：PDF 预览功能问题修复

**日期**: 2026-02-27
**版本**: v0.6
**状态**: ✅ 已修复

---

## 问题描述

在 2026-02-27 的文件加载性能优化实施中，PDF 预览功能存在以下严重问题：

### 发现的问题（第一轮）

| 优先级 | 问题 | 影响 |
|--------|------|------|
| 🔴 严重 | 重复读取文件 | PDF 文件被读取 2 次，性能灾难 |
| 🔴 严重 | 未使用 file:// URL | 优化方案完全未生效 |
| 🟡 中等 | 代码缩进错误 | 可读性差 |
| 🟡 中等 | 未释放 pdfDoc 资源 | 内存泄漏风险 |
| 🟢 轻微 | loadPdf 重复触发 | watch + onMounted 导致调用 2 次 |

### 发现的问题（第二轮调试）

| 优先级 | 问题 | 影响 |
|--------|------|------|
| 🔴 严重 | file:// 被安全策略阻止 | Electron 不允许直接加载 file:// URL |
| 🔴 严重 | Canvas 元素未找到 | DOM 渲染时序问题 |

---

## 问题根源

### 第一轮问题
1. **PdfViewer.vue 中的逻辑错误**：优先使用 `filePath` 但没有用 `file://` URL，反而又调了一次 `readBinaryFile`
2. **document store 仍预加载二进制文件**：虽然我们有了 filePath，但 store 还是会读取 base64
3. **代码质量问题**：缩进不一致，缺少资源清理

### 第二轮问题
1. **Electron 安全策略**：`webSecurity` 默认阻止 `file://` URL 跨域加载
2. **DOM 渲染时序**：canvas 被 `v-else="isLoading"` 包裹，但在 `isLoading` 设为 false 前就尝试访问

---

## 修复内容

### 修改的文件

| 文件 | 变更 |
|------|------|
| `app/src/components/PdfViewer.vue` | 完全重写 + 协议切换 + 时序修复 |
| `app/src/stores/document.js` | 移除二进制文件预加载 |
| `app/electron/main.js` | 注册 local-file:// 协议 + PDF MIME 类型 |

---

## 技术细节

### 1. 自定义协议方案

```javascript
// electron/main.js
protocol.registerSchemesAsPrivileged([
  { scheme: 'local-file', privileges: { standard: true, secure: true, supportFetchAPI: true } }
])

protocol.handle('local-file', (request) => {
  const filePath = decodeURIComponent(request.url.slice('local-file://'.length))
  const normalizedPath = filePath.replace(/^([a-zA-Z])(?=\/)/, '$1:').replace(/\//g, '\\')
  const fileStream = fs.createReadStream(normalizedPath)
  return new Response(fileStream, { headers: { 'Content-Type': mimeType } })
})
```

### 2. PdfViewer.vue 修复要点

```javascript
// 使用 local-file:// 代替 file://
if (props.filePath) {
  const formattedPath = props.filePath.replace(/\\/g, '/')
  const url = `local-file://${formattedPath.replace(/^\/+/, '')}`
  loadingTask = pdfjsLib.getDocument({ url })
}

// 修复 DOM 时序问题
pdfDoc.value = await loadingTask.promise
totalPages.value = pdfDoc.value.numPages
currentPage.value = 1

isLoading.value = false  // 先让 canvas 渲染出来
await nextTick()          // 等待 DOM 更新
await renderPage(currentPage.value)

// 添加资源释放
onUnmounted(() => {
  if (pdfDoc.value) {
    pdfDoc.value.destroy()
  }
})
```

### 3. document.js 优化

```javascript
// 不再预加载二进制文件
if (!isBinaryFile.value) {
  // 只加载 Markdown
}
// PDF/音视频直接通过 filePath 访问，无需预加载
```

---

## 完整修复时间线

| 时间 | 事件 |
|------|------|
| 第一轮 | 修复重复读取、代码质量等问题 |
| 错误 1 | `Not allowed to load local resource` |
| 修复 1 | 改用 `local-file://` 自定义协议 |
| 错误 2 | `Canvas 元素未找到` |
| 修复 2 | 调整 DOM 渲染时序 |

---

## 性能对比

| 指标 | 修复前 | 修复后 |
|------|--------|--------|
| PDF 文件读取次数 | 2 次 | 0 次（通过协议流式加载） |
| IPC 通信量 | 整个文件 | 几乎为 0 |
| 内存占用 | 高（base64 + 重复） | 低（pdf.js 按需加载） |
| loadPdf 触发次数 | 2 次 | 1 次 |
| 协议 | file://（被阻止） | local-file://（自定义） |

---

## 验证测试

测试步骤：
1. 启动应用：`npm run start`
2. 打开 PDF 文件 - 验证加载速度
3. 打开视频文件 - 验证流式播放
4. 在 PDF 和其他文件间切换 - 验证无内存泄漏
