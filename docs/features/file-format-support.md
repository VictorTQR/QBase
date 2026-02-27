# 文件格式支持

**状态**: ✅ 已完成
**版本**: v0.6

---

## 概述

QBase 现在支持多种文件格式，除了 Markdown 之外，还包括 PDF、音频和视频文件。

**v0.6 优化**：从 Base64 编码传输改为直接 `file://` 协议访问，大幅提升大文件加载性能。

---

## 支持的格式

### 文档格式

| 格式 | 扩展名 | 查看器 | 说明 |
|------|--------|--------|------|
| Markdown | `.md` | MarkdownViewer | 支持 LaTeX、代码高亮、Mermaid |
| PDF | `.pdf` | PdfViewer | 支持翻页、缩放 |

### 音频格式

| 格式 | 扩展名 | 说明 |
|------|--------|------|
| MP3 | `.mp3` | MPEG Audio Layer III |
| WAV | `.wav` | Waveform Audio |
| OGG | `.ogg` | Ogg Vorbis |
| M4A | `.m4a` | MPEG-4 Audio |
| FLAC | `.flac` | Free Lossless Audio Codec |

### 视频格式

| 格式 | 扩展名 | 说明 |
|------|--------|------|
| MP4 | `.mp4` | MPEG-4 Video |
| WebM | `.webm` | WebM Video |
| MOV | `.mov` | QuickTime Movie |
| MKV | `.mkv` | Matroska Video（浏览器兼容性取决于系统） |

---

## 技术架构

### 文件加载策略（v0.6 优化）

| 文件类型 | 加载方式 | 说明 |
|---------|---------|------|
| Markdown | `readFile()` | UTF-8 文本读取 |
| PDF | `file://` URL | pdfjs-dist 直接加载 |
| 音视频 | `file://` URL | HTML5 原生播放器流式播放 |

### 性能对比

| 指标 | Base64 方案（旧） | file:// 方案（新） |
|------|-----------------|-------------------|
| 内存占用 | 高（增加 33%） | 低（直接文件映射） |
| 大视频加载 | 需等待完整传输 | 即时播放 |
| IPC 通信量 | 大（整个文件） | 几乎为 0 |
| 流式播放 | ❌ 不支持 | ✅ 支持 |

### 自定义协议

Electron 主进程注册了 `local-file://` 自定义协议（预留，当前使用 `file://`）：

```javascript
// electron/main.js
protocol.registerSchemesAsPrivileged([
  { scheme: 'local-file', privileges: { standard: true, secure: true, supportFetchAPI: true } }
])

protocol.handle('local-file', (request) => {
  const filePath = request.url.slice('local-file://'.length)
  return net.fetch(`file:///${filePath}`)
})
```

---

## 组件说明

### DocumentViewer

统一文档查看器，根据文件类型自动分发到对应的查看器。

**位置**: `src/components/DocumentViewer.vue`

**Props 传递**:
- `filePath`: 优先使用文件路径
- `base64Data`: 向后兼容，保留 Base64 支持

### PdfViewer

PDF 查看器组件，基于 `pdfjs-dist`。

**位置**: `src/components/PdfViewer.vue`

**功能**:
- 翻页（上一页/下一页）
- 缩放（0.5x - 3x）
- 页面进度显示
- 支持 `filePath` 和 `base64Data` 两种输入

**加载逻辑**:
```javascript
if (props.filePath) {
  const url = `file:///${formattedPath}`
  loadingTask = pdfjsLib.getDocument({ url })
} else if (props.base64Data) {
  // 旧的 Base64 逻辑
}
```

### MediaViewer

音视频播放器组件，使用原生 HTML5 标签。

**位置**: `src/components/MediaViewer.vue`

**功能**:
- 播放/暂停
- 进度条
- 音量控制
- 全屏（视频）
- 支持 `filePath` 和 `base64Data` 两种输入

**URL 构造**:
```javascript
if (props.filePath) {
  const formattedPath = props.filePath.replace(/\\/g, '/')
  return `file:///${formattedPath.replace(/^\/+/, '')}`
}
```

---

## 使用方法

1. 将支持的文件放入工作区文件夹
2. 在左侧文件树中点击文件
3. 中间面板会自动使用对应的查看器打开

---

## 向后兼容性

所有组件仍支持原有的 `base64Data` prop，确保旧代码可以正常运行。

---

## 后续扩展

- PDF 文本搜索
- PDF 文本选择和复制
- 分页懒加载（大 PDF 优化）
- 更多音视频格式支持（如需要额外解码器）
