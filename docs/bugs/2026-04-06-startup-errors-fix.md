# 2026-04-06 项目启动错误修复

## 问题概述

本次修复解决了 QBase 项目启动过程中的多个关键错误，包括后端导入错误、Electron API 弃用问题和 SQLAlchemy 表定义冲突。

## 修复的问题

### 1. 后端导入错误 - `compute_bytes_hash`

**问题描述**：
```
ImportError: cannot import name 'compute_bytes_hash' from 'utils.file_hash'
```

**原因**：
- `task_manager.py` 中尝试导入 `compute_bytes_hash` 函数
- 但 `file_hash.py` 中该函数实际命名为 `compute_short_hash`

**修复方案**：
- 将 `file_hash.py` 中的 `compute_short_hash` 重命名为 `compute_bytes_hash`

**修改文件**：
- `backend/src/utils/file_hash.py`

---

### 2. 文件哈希函数 - 同步/异步版本问题

**问题描述**：
- 部分代码使用 `await compute_file_hash()`
- 部分代码直接调用 `compute_file_hash()`
- 导致类型不匹配和运行时错误

**修复方案**：
- 创建 `compute_file_hash_sync()` - 纯同步版本
- 创建 `compute_file_hash()` - 异步版本（使用线程池包装同步版本）
- 更新所有调用点，根据上下文使用正确版本

**修改文件**：
- `backend/src/utils/file_hash.py`
- `backend/src/api/files.py`
- `backend/src/api/workspace.py`
- `backend/src/api/derivatives.py`
- `backend/src/services/workspace_service.py`
- `backend/src/services/file_scanner.py`

---

### 3. 前端 `@electron/remote` 弃用错误

**问题描述**：
```
Failed to resolve import "@electron/remote" from "src/utils/workspaceManager.js"
```

**原因**：
- `@electron/remote` 包已被弃用
- 当前 Electron 版本使用 contextBridge 和 IPC 通信

**修复方案**：
1. 在 `preload.js` 中添加新的 IPC 方法：
   - `getHomePath()` - 获取用户主目录
   - `fsExists()` - 检查文件/目录是否存在
   - `fsMkdir()` - 创建目录
   - `fsReadFile()` - 读取文件
   - `fsWriteFile()` - 写入文件

2. 在 `main.js` 中实现这些 IPC 处理器

3. 重写 `workspaceManager.js`：
   - 移除 `@electron/remote` 依赖
   - 使用 `window.electronAPI` 进行文件系统操作
   - 改为异步设计模式

4. 更新相关 store 和组件：
   - `workspace.js` store 添加 `ensureInitialized()` 方法
   - `App.vue` 使用 `await` 调用初始化

**修改文件**：
- `app/electron/preload.js`
- `app/electron/main.js`
- `app/src/utils/workspaceManager.js`
- `app/src/stores/workspace.js`
- `app/src/App.vue`

---

### 4. `async_session` 导入错误

**问题描述**：
```
ImportError: cannot import name 'async_session' from 'src.database'
```

**原因**：
- `database.py` 中导出的是 `AsyncSessionLocal`
- 但其他文件尝试导入 `async_session`

**修复方案**：
- 将所有 `async_session` 导入和使用替换为 `AsyncSessionLocal`

**修改文件**：
- `backend/src/api/mineru.py`
- `backend/src/api/files.py`
- `backend/src/api/workspace.py`
- `backend/src/api/derivatives.py`
- `backend/src/services/workspace_service.py`

---

### 5. Python 缩进错误

**问题描述**：
```
IndentationError: unindent does not match any outer indentation level
```

**原因**：
- `workspace_service.py` 中 `_process_file` 方法前有多余的空格

**修复方案**：
- 修正缩进，使用 4 空格标准缩进

**修改文件**：
- `backend/src/services/workspace_service.py`

---

### 6. SQLAlchemy 表重复定义错误

**问题描述**：
```
sqlalchemy.exc.InvalidRequestError: Table 'parse_tasks' is already defined for this MetaData instance.
Specify 'extend_existing=True' to redefine options and columns on an existing Table object.
```

**原因**：
- 模块被多次导入导致 SQLAlchemy MetaData 中表定义冲突
- 开发模式下 Uvicorn 重新加载器会导致模块重复导入

**修复方案**：
- 为所有数据库模型类添加 `__table_args__ = {'extend_existing': True}`
- 对于已有 `UniqueConstraint` 的表，将 `extend_existing` 合并到同一 `__table_args__` 中

**修改文件**：
- `backend/src/models/db_models.py`

**受影响的表**：
1. `parse_tasks` (ParseTask)
2. `papers` (DBPaper)
3. `paper_keywords` (DBPaperKeyword)
4. `files` (DBFile)
5. `derivatives` (DBDerivative)
6. `tasks` (DBTask)

---

## 修复验证

### 后端启动验证
- [x] Uvicorn 能够正常启动
- [x] 所有 API 路由能够正常导入
- [x] 数据库模型能够正常初始化
- [x] 没有导入错误或运行时错误

### 前端启动验证
- [x] Vite 能够正常启动
- [x] Electron API 能够正常通信
- [x] Workspace manager 能够正常初始化
- [x] 没有模块解析错误

---

## 技术要点

### 1. SQLAlchemy `extend_existing` 参数
- 作用：允许表定义被重新定义而不抛出错误
- 使用场景：开发模式下的热重载、模块多次导入
- 注意：仅在开发环境有用，生产环境应避免模块重复导入

### 2. Electron ContextBridge 安全模式
- 不再使用 `@electron/remote`
- 通过 `contextBridge.exposeInMainWorld` 暴露受限制的 API
- 所有文件系统操作通过 IPC 进行
- 符合 Electron 安全最佳实践

### 3. 异步文件哈希计算
- 同步版本：`compute_file_hash_sync()` - 用于非异步上下文
- 异步版本：`compute_file_hash()` - 使用 `loop.run_in_executor()` 在线程池中运行
- 根据调用上下文选择合适版本

---

## 相关文档

- [AGENTS.md](../../AGENTS.md) - AI 代理开发指南
- [architecture/system-architecture.md](../architecture/system-architecture.md) - 系统架构设计

---

**修复日期**：2026-04-06  
**修复状态**：✅ 已完成  
**影响版本**：v1.1+
