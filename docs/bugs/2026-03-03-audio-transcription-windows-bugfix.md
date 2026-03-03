# 音频转录接口 Bug 修复记录

**日期**: 2026-03-03  
**状态**: ✅ 已修复  
**影响版本**: v1.0 (音频转录功能)

## 问题描述

在 `/docs` 页面测试 `/api/audio/transcribe-upload` 接口时，返回 500 Internal Server Error。

### 原始错误日志
```
INFO:     127.0.0.1:49690 - "POST /api/audio/transcribe-upload HTTP/1.1" 500 Internal Server Error
```

错误信息不完整，只记录了空字符串。

---

## 问题诊断

通过添加详细调试日志和堆栈跟踪，发现了多个问题：

### 问题 1: 导入路径错误
**位置**: `backend/src/processors/audio_processor.py:140`

**错误代码**:
```python
from ..audio.utils import merge_transcriptions
```

**原因**: 相对导入路径不正确，该文件已经通过 `sys.path.insert()` 添加了 `src` 目录到路径中。

**修复**:
```python
from audio.utils import merge_transcriptions
```

---

### 问题 2: Windows asyncio subprocess 兼容性
**位置**: `backend/src/audio/chunker.py`

**错误**:
```
NotImplementedError
```

**错误堆栈**:
```
File "asyncio/base_events.py", line 528, in _make_subprocess_transport
    raise NotImplementedError
```

**原因**: Windows 平台的 `_WindowsSelectorEventLoop` 不支持 `asyncio.create_subprocess_exec()`。

**修复**: 使用同步的 `subprocess.run()` + `asyncio.to_thread()` 在后台线程中运行。

**修改内容**:
1. `get_audio_duration()` 方法 - 改用同步 subprocess
2. `_split_audio()` 方法 - 改用同步 subprocess

---

### 问题 3: 音频编码转换错误
**位置**: `backend/src/audio/chunker.py`

**错误**:
```
[mp3 @ ...] Invalid audio stream. Exactly one MP3 audio stream is required.
[out#0/mp3 @ ...] Could not write header (incorrect codec parameters ?): Invalid argument
Conversion failed!
```

**原因**: 使用 `-c copy` 直接复制 AAC 流到 MP3 容器，这是不兼容的。

**修复**:
```bash
# 之前
-c copy

# 修复后
-c:a libmp3lame -ar 16000
```

**参数说明**:
- `-c:a libmp3lame` - 使用 LAME MP3 编码器重新编码
- `-ar 16000` - 设置采样率为 16kHz（ASR 模型最佳实践）

---

### 问题 4: 错误日志不完整
**位置**: `backend/src/api/audio.py:55`

**问题**: 使用 `logger.error()` 只记录错误消息，没有堆栈跟踪。

**修复**:
```python
# 之前
logger.error(f"音频上传转录失败: {e}")

# 修复后
logger.exception(f"音频上传转录失败: {e}")
```

---

## 额外改进

### 启动时健康检查
**文件**: `backend/main.py`

在启动时添加了以下检查：
- ✅ ffprobe 是否安装
- ✅ ffmpeg 是否安装
- ✅ SILICONFLOW_API_KEY 是否已配置
- ✅ MINERU_API_KEY 是否已配置

### 详细调试日志
在关键位置添加了 `logger.debug()` 日志：
- 音频上传处理步骤
- 临时文件创建
- 任务创建过程
- 文件大小和时长信息

---

## 修复文件清单

| 文件 | 修改内容 |
|------|---------|
| `backend/src/processors/audio_processor.py` | 修复导入路径错误 |
| `backend/src/api/audio.py` | 改进错误日志 + 添加调试日志 |
| `backend/src/audio/chunker.py` | Windows 兼容性 + 音频编码修复 |
| `backend/main.py` | 添加启动健康检查 |

---

## 测试验证

### 测试步骤
1. 重启后端服务器
2. 访问 `/docs` 页面
3. 上传音频文件测试 `/api/audio/transcribe-upload` 接口
4. 观察日志输出

### 预期结果
```
==================================================
执行启动健康检查...
✓ ffprobe 检查通过
✓ ffmpeg 检查通过
✓ SILICONFLOW_API_KEY 已配置
✓ MINERU_API_KEY 已配置
==================================================
```

接口返回 200 OK，并创建转录任务。

---

## 根因分析

本次问题是**多因素导致**的：

1. **开发环境差异** - 代码在非 Windows 环境开发，未考虑 Windows 平台 asyncio 限制
2. **导入路径混乱** - 同时使用 sys.path 操作和相对导入，导致冲突
3. **FFmpeg 参数理解不足** - `-c copy` 只能用于相同编码格式的容器转换
4. **错误处理不完善** - 缺少堆栈跟踪，增加了调试难度

---

## 预防措施

1. **跨平台测试** - 在 Windows、Linux、macOS 上测试关键功能
2. **统一导入规范** - 避免混合使用 sys.path 和相对导入
3. **FFmpeg 最佳实践** - 需要转码时明确指定编码器
4. **完善错误日志** - 始终使用 `logger.exception()` 记录异常
5. **启动健康检查** - 在应用启动时验证关键依赖

---

## 相关文档

- [音频转录功能实现](../implementation/2026-03-02-audio-transcription.md)
- [音频 API 统一重构](../implementation/2026-03-03-audio-api-unification.md)
