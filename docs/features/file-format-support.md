# 文件格式支持

**状态**: ✅ 已完成
**版本**: v0.4

---

## 概述

QBase 现在支持多种文件格式，除了 Markdown 之外，还包括 PDF、音频和视频文件。

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

## 组件说明

### DocumentViewer

统一文档查看器，根据文件类型自动分发到对应的查看器。

**位置**: `src/components/DocumentViewer.vue`

### PdfViewer

PDF 查看器组件，基于 `pdfjs-dist`。

**位置**: `src/components/PdfViewer.vue`

**功能**:
- 翻页（上一页/下一页）
- 缩放（0.5x - 3x）
- 页面进度显示

**预留接口**:
- 分页懒加载（大文件优化）
- 文本搜索
- 文本选择和复制

### MediaViewer

音视频播放器组件，使用原生 HTML5 标签。

**位置**: `src/components/MediaViewer.vue`

**功能**:
- 播放/暂停
- 进度条
- 音量控制
- 全屏（视频）

---

## 使用方法

1. 将支持的文件放入工作区文件夹
2. 在左侧文件树中点击文件
3. 中间面板会自动使用对应的查看器打开

---

## 后续扩展

- PDF 文本搜索
- PDF 文本选择和复制
- 分页懒加载（大 PDF 优化）
- 更多音视频格式支持（如需要额外解码器）
