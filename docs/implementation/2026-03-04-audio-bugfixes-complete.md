# 音频功能 Bug 修复完成报告

**日期**: 2026-03-04  
**版本**: v1.0  
**状态**: ✅ 已完成

---

## 概述

本次修复解决了音频转录功能中的多个 bug，包括：
1. 音频分块状态一直是 pending 的问题
2. 同一个音频文件上传 hash 值不一致的问题
3. 音频去重返回后 task_id 不一致的问题
4. _create_task() 忽略 add_task() 返回值的问题

---

## 修复的问题清单

### 1. ✅ 音频分块状态一直是 pending

**问题描述**: `/api/audio/tasks/{task_id}` 接口中的 chunks 字段的任务状态 status 一直是 pending。

**问题根因**: 在 `_parse_task_to_audio_info` 方法中，对 chunk 状态也调用了 `_map_state_to_status()` 方法，但这个方法是用来映射统一状态（"pending"/"running"/"done"/"failed"）的，而 chunk 状态存储的是 `AudioTaskStatus` 枚举值本身。

**修复方案**:
- 移除对 chunk 状态的 `_map_state_to_status()` 转换
- 直接读取存储的状态字符串
- 通过匹配枚举值将字符串转换为 `AudioTaskStatus` 枚举

**修改文件**: `backend/src/audio/task_manager.py:76-91`

**提交**: `4fe8cbf`

---

### 2. ✅ 同一个音频文件上传 hash 值不一致

**问题描述**: 使用 `/api/audio/transcribe-upload` 时，上传同一个音频文件，计算出来的 hash 值不一致。

**问题根因**: 在 `audio/task_manager.py:142` 中，file_hash 是用 `f"audio_{task_info.task_id}"` 生成的，而 task_id 每次都是新的 UUID，所以同一个文件每次上传都会有不同的 hash。

**对比文档解析**: 文档解析在 `mineru/task_manager.py:46-52` 中使用 `compute_bytes_hash(content)` 或 `compute_file_hash(file_path)` 计算 hash。

**修复方案**:
- 在 `AudioProcessor.process()` 中添加 hash 计算
- 在 `AudioProcessor._create_task()` 中添加备用 hash 计算
- 在 `AudioTaskManager.add_task()` 中使用传递的 hash
- 添加去重检查逻辑

**修改文件**:
- `backend/src/processors/audio_processor.py`
- `backend/src/api/audio.py`
- `backend/src/audio/task_manager.py`

**提交**:
- `0bf482c` - 功能: 为 AudioProcessor 添加文件 hash 计算
- `e8fe5e7` - 功能: 传递 file_content 给 audio_processor.process
- `869240a` - 功能: 在 AudioTaskManager 中使用基于内容的 file_hash 并添加去重

---

### 3. ✅ 音频去重返回后 task_id 不一致

**问题描述**: 去重检查成功后，返回给前端的 task_id 是新生成的，而不是已有任务的 task_id，导致后台处理用新的 task_id 去查找，当然找不到。

**问题根因**:
1. `AudioTaskManager.add_task()` 去重时返回 `ParseTask` 对象，新建时返回 `AudioTaskInfo`，类型不一致
2. `AudioProcessor.process()` 不管 `add_task()` 返回什么，都用新的 `task_id`

**修复方案**:
- 修改 `AudioTaskManager.add_task()` 统一返回 `AudioTaskInfo`
- 修改 `AudioProcessor.process()` 检查返回值，如果是去重返回，直接返回已有任务信息

**修改文件**:
- `backend/src/audio/task_manager.py`
- `backend/src/processors/audio_processor.py`

**提交**:
- `532c384` - 修复: 统一 add_task() 返回类型为 AudioTaskInfo
- `492658d` - 修复: 检查 add_task() 返回值，去重时不启动后台处理

---

### 4. ✅ _create_task() 忽略 add_task() 返回值

**问题描述**: 尽管 `add_task()` 返回了已有任务，但是 `_create_task()` 方法仍然返回新创建的 `task` 对象。

**问题根因**: 在 `_create_task()` 方法中，调用了 `add_task()` 但没有使用返回值，而是直接返回了新创建的 `task`。

**修复方案**: 修改 `_create_task()` 方法，保存 `add_task()` 的返回值并返回它。

**修改文件**: `backend/src/processors/audio_processor.py:103-104`

**提交**: `45f9406` - 修复: 从 _create_task() 返回 add_task() 的实际返回值

---

## 修改文件清单

### 修改的文件（7个）

| 文件 | 修改次数 | 说明 |
|------|---------|------|
| `backend/src/audio/task_manager.py` | 3次 | 分块状态修复、hash使用、返回类型统一 |
| `backend/src/processors/audio_processor.py` | 4次 | hash计算、返回值检查、_create_task修复 |
| `backend/src/api/audio.py` | 1次 | 传递file_content |

---

## 提交记录

```
45f9406 修复: 从 _create_task() 返回 add_task() 的实际返回值
492658d 修复: 检查 add_task() 返回值，去重时不启动后台处理
532c384 修复: 统一 add_task() 返回类型为 AudioTaskInfo
e851538 backup: before fix create_task return value
a91d26e backup: before audio duplicate return fix
869240a 功能: 在 AudioTaskManager 中使用基于内容的 file_hash 并添加去重
e8fe5e7 功能: 传递 file_content 给 audio_processor.process
0bf482c 功能: 为 AudioProcessor 添加文件 hash 计算
34132c5 backup: before audio file hash fix
4fe8cbf 修复: 修复音频分块状态一直是 pending 的问题
```

---

## 功能验证清单

### 已验证功能
- [x] 音频分块状态正确显示（pending/transcribing/completed/failed）
- [x] 同一个文件上传两次，hash 值相同
- [x] 去重检查正常工作
- [x] 去重后返回已有任务的 task_id
- [x] 去重后不启动后台处理
- [x] 没有"任务不存在"错误
- [x] 音频转录功能正常工作

---

## 相关文档

- [修复音频分块状态 bug 记录](../bugs/2026-03-04-audio-chunk-status-pending.md)
- [修复音频文件 hash 不一致计划](../plans/2026-03-04-fix-audio-file-hash.md)
- [修复音频去重返回 bug 计划](../plans/2026-03-04-fix-audio-duplicate-return-bug.md)
- [修复 _create_task() 返回值计划](../plans/2026-03-04-fix-create-task-return-value.md)
