# 实施报告：文件加载性能优化

**日期**: 2026-02-27
**版本**: v0.6
**状态**: ✅ 已完成

---

## 问题描述

在 v0.5 及之前版本中，PDF、音频、视频等二进制文件采用 Base64 编码方式在 Electron 主进程和渲染进程间传输，存在以下问题：

| 问题 | 影响 |
|------|------|
| 内存占用高 | Base64 编码使体积增加约 33% |
| 大文件加载慢 | 视频/PDF 需要完全加载到内存 |
| 无流式播放 | 视频无法边下边播 |
| IPC 通信压力大 | 大数据在进程间传输 |

---

## 解决方案

采用 `file://` 协议直接访问本地文件系统路径，组件直接通过 URL 加载文件。

### 方案选择

| 方案 | 优点 | 缺点 | 选择 |
|------|------|------|------|
| 自定义协议 `local-file://` | 安全可控 | 实现稍复杂 | 已注册（预留） |
| 直接 `file://` 协议 | 简单高效 | - | ✅ 采用 |
| 禁用 webSecurity | 最简单 | 有安全风险 | ❌ 不采用 |

---

## 实施内容

### 修改的文件

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `app/electron/main.js` | 新增 | 注册 `local-file://` 自定义协议 |
| `app/src/components/PdfViewer.vue` | 修改 | 新增 `filePath` prop，支持 URL 加载 |
| `app/src/components/MediaViewer.vue` | 修改 | 新增 `filePath` prop，使用 `file://` URL |
| `app/src/components/DocumentViewer.vue` | 修改 | 传递 `filePath` 给子组件 |
| `docs/features/file-format-support.md` | 更新 | 文档更新 |

---

## 技术细节

### 1. Electron 协议注册

```javascript
// electron/main.js
const { protocol, net } = require('electron')

protocol.registerSchemesAsPrivileged([
  { scheme: 'local-file', privileges: { standard: true, secure: true, supportFetchAPI: true } }
])

app.whenReady().then(() => {
  protocol.handle('local-file', (request) => {
    const filePath = request.url.slice('local-file://'.length)
    return net.fetch(`file:///${filePath}`)
  })
})
```

### 2. MediaViewer 实现

```javascript
const mediaSrc = computed(() => {
  if (props.filePath) {
    const formattedPath = props.filePath.replace(/\\/g, '/')
    return `file:///${formattedPath.replace(/^\/+/, '')}`
  }
  if (props.base64Data) {
    return `data:${props.mimeType};base64,${props.base64Data}`
  }
  return ''
})
```

### 3. PdfViewer 实现

```javascript
if (props.filePath) {
  const formattedPath = props.filePath.replace(/\\/g, '/')
  const url = `file:///${formattedPath.replace(/^\/+/, '')}`
  loadingTask = pdfjsLib.getDocument({ url })
} else if (props.base64Data) {
  // 向后兼容
}
```

---

## 向后兼容性

✅ **完全兼容** - 所有组件仍支持原有的 `base64Data` prop，旧代码不会受影响。

---

## 性能预期

| 指标 | 预期改善 |
|------|---------|
| 大视频加载时间 | 从「几秒」→「即时」 |
| 内存占用 | 降低约 50-70% |
| 视频拖动响应 | 流畅流式播放 |
| IPC 通信量 | 几乎为 0 |

---

## 测试验证

测试步骤：
1. 启动应用：`npm run start`
2. 测试 PDF 文件（>10MB）
3. 测试视频文件（>100MB）
4. 测试音频文件
5. 验证 Markdown 仍正常工作

---

## 相关文档

- [功能文档：文件格式支持](../features/file-format-support.md)
