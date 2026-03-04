# 统一数据存储重构实施报告

**日期**: 2026-03-04  
**版本**: v1.0  
**状态**: ✅ 已完成

---

## 概述

本次重构实现了统一的数据存储架构，将文档解析和音频转录任务都存储在同一个 SQLite 数据库表中，并优化了向量索引流程，避免传输大文本内容。

**主要目标**:
- 统一 ParseTask 表结构，支持多种文件类型
- 音频任务从内存存储迁移到 SQLite 数据库
- 向量索引支持通过 task_id 从数据库获取内容

---

## 实施内容

### 1. ✅ 扩展 ParseTask 数据模型

**变更内容**:
- 添加 `file_type` 字段（默认值: "document"）
- 添加 `task_metadata` 字段（用于存储 JSON 格式的元数据）
- 注意：`metadata` 是 SQLAlchemy 保留字，故使用 `task_metadata`

**修改文件**: `backend/src/models/db_models.py`

**提交**: `b4bc494`, `0a83200`

---

### 2. ✅ 扩展 ParseTaskRepository

**新增方法**:
- `list_by_type(file_type, limit, offset)` - 按文件类型列出任务
- `get_stats_by_type(file_type)` - 按文件类型获取统计

**修改文件**: `backend/src/repositories/parse_task_repository.py`

**提交**: `03ea861`

---

### 3. ✅ 重写音频任务管理器

**变更内容**:
- 完全重写 `AudioTaskManager`，从内存存储改为数据库存储
- 保持公共接口不变，确保向后兼容
- 添加状态映射：`AudioTaskStatus` ↔ 统一状态（pending/running/done/failed）
- 实现同步/异步包装方法
- 支持 WebSocket 实时更新

**关键方法**:
- `_parse_task_to_audio_info()` - 数据库模型转 AudioTaskInfo
- `add_task()` - 添加任务到数据库
- `get_task()` / `_get_task_async()` - 获取任务
- `update_task()` / `_update_task_async()` - 更新任务
- `remove_task()` / `_remove_task_async()` - 删除任务
- `get_all_tasks()` / `_get_all_tasks_async()` - 获取所有任务

**修改文件**: `backend/src/audio/task_manager.py`

**提交**: `266b629`, `0a83200`

---

### 4. ✅ 更新文档任务管理器

**变更内容**:
- `_task_to_dict()` 方法添加 `file_type` 和 `metadata` 字段
- `create_task()` 方法设置 `file_type` 为 "document"

**修改文件**: `backend/src/mineru/task_manager.py`

**提交**: `4fe0ca5`, `0a83200`

---

### 5. ✅ 扩展向量索引 Schema

**变更内容**:
- `VectorIndexRequest` 类添加 `task_id` 字段（可选）
- `content` 字段改为可选

**修改文件**: `backend/src/vector/schemas.py`

**提交**: `04e586b`

---

### 6. ✅ 修改向量索引 API

**变更内容**:
- 添加数据库相关导入
- 支持从 `task_id` 获取内容，优先级高于请求中的 `content`
- 验证内容存在性
- 保持原有功能不变

**修改文件**: `backend/src/api/vector.py`

**提交**: `66df25c`

---

### 7. ✅ 修改前端向量 Store

**变更内容**:
- `indexDocument()` 函数添加 `taskId` 参数
- 支持通过 `taskId` 或 `content` 两种方式索引
- `indexBatch()` 函数直接传 `task.id`，移除 `getExtractedTextFn` 调用

**修改文件**: `app/src/stores/vector.js`

**提交**: `23e3a6f`

---

### 8. ✅ 修改前端解析页面

**变更内容**:
- `handleIndexDocument()` 直接传 `task.id`
- `handleBatchIndex()` 移除 `getExtractedTextFn` 参数

**修改文件**: `app/src/components/parse/ParseDocumentsView.vue`

**提交**: `714171a`

---

### 9. ✅ 修复 SQLAlchemy 保留字冲突

**问题描述**: `metadata` 是 SQLAlchemy Declarative API 的保留属性名，导致启动错误。

**修复方案**: 将字段名从 `metadata` 改为 `task_metadata`

**修改文件**:
- `backend/src/models/db_models.py`
- `backend/src/mineru/task_manager.py`
- `backend/src/audio/task_manager.py`

**提交**: `0a83200`

---

## 修改文件清单

### 修改文件（8个）

| 文件 | 说明 |
|------|------|
| `backend/src/models/db_models.py` | 扩展 ParseTask 表结构 |
| `backend/src/repositories/parse_task_repository.py` | 添加按类型查询方法 |
| `backend/src/audio/task_manager.py` | 重写为数据库存储 |
| `backend/src/mineru/task_manager.py` | 添加 file_type 支持 |
| `backend/src/vector/schemas.py` | 添加 task_id 字段 |
| `backend/src/api/vector.py` | 支持通过 task_id 获取内容 |
| `app/src/stores/vector.js` | 支持 taskId 参数 |
| `app/src/components/parse/ParseDocumentsView.vue` | 使用 taskId 索引 |

---

## 提交记录

```
0a83200 修复: 将 metadata 字段重命名为 task_metadata 以避免 SQLAlchemy 保留字冲突
714171a 重构: 使用 taskId 代替 content 进行向量索引
23e3a6f 重构: 为向量 store 添加 taskId 参数支持
66df25c 重构: 支持通过 task_id 从数据库获取内容进行索引
04e586b 重构: 为 VectorIndexRequest 添加 task_id，使 content 变为可选
4fe0ca5 重构: 为 mineru 任务管理器添加 file_type 字段
266b629 重构: 重写 AudioTaskManager 以使用数据库存储
03ea861 重构: 为 repository 添加 list_by_type 和 get_stats_by_type
b4bc494 重构: 扩展 ParseTask，添加 file_type 和 metadata
f2c64a0 backup: before unified storage refactor
```

---

## 功能验证清单

### 待验证功能
- [ ] 后端启动无错误
- [ ] 文档解析正常工作，file_type = "document"
- [ ] 音频转录正常工作，file_type = "audio"
- [ ] 音频任务持久化（重启后端不丢失）
- [ ] 向量索引通过 task_id 工作
- [ ] 网络请求中无大文本 content 传输
- [ ] WebSocket 实时更新正常

---

## 架构变更

### 数据库表结构变更

**ParseTask 表新增字段**:
```python
file_type = Column(String, nullable=False, default="document", index=True)
task_metadata = Column(Text, nullable=True)
```

### 数据流程变更

**向量索引旧流程**:
1. 前端提取文档内容
2. 前端发送大文本 content 到后端
3. 后端接收并处理

**向量索引新流程**:
1. 前端发送 task_id 到后端
2. 后端通过 task_id 从数据库获取内容
3. 后端处理内容并索引

---

## 相关文档

- [统一数据存储重构计划](../plans/2026-03-03-unified-storage-refactor.md)
- [解析管理功能文档](../features/parse-management.md)
