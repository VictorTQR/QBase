# 2026-04-06 工作区数据和 SQLAlchemy 模型冲突修复

## 问题概述

本次修复解决了 QBase 项目运行时的多个问题，包括前端工作区数据损坏导致的类型错误、后端 SQLAlchemy 模型重复定义冲突，以及论文模块数据库初始化问题。

## 修复的问题

### 1. 前端工作区数据类型错误

**问题描述**：
```
Uncaught (in promise) TypeError: currentWorkspace.value.split is not a function
    at ComputedRefImpl.fn (workspace.js:17:37)
```

**原因**：
- Pinia 持久化存储中保存了非字符串类型的 `currentWorkspace` 值（数字 `2`）
- 多处代码未对 `currentWorkspace` 进行类型验证就调用字符串方法

**修复方案**：
1. 在 `workspaceName` 计算属性中添加类型检查
2. 在 `initializeAndScanWorkspace` 中添加路径验证
3. 添加 `fixCorruptedWorkspace()` 函数自动修复损坏数据
4. 在应用启动和组件挂载时调用修复函数

**修改文件**：
- `app/src/stores/workspace.js`
- `app/src/stores/fileManagement.js`
- `app/src/utils/workspaceManager.js`
- `app/src/components/Layout/Sidebar.vue`
- `app/src/App.vue`

---

### 2. 后端 API 422 错误处理改进

**问题描述**：
```
POST http://localhost:8000/api/workspace/initialize 422 (Unprocessable Entity)
```

**原因**：
- 错误处理代码未能正确解析 Pydantic 验证错误格式
- 当 `data.detail` 是对象或数组时，错误信息显示为 `[object Object]`

**修复方案**：
- 改进 `workspaceBackend.js` 中的错误处理逻辑
- 支持多种错误格式（字符串、数组、对象）
- 提供更友好的错误信息显示

**修改文件**：
- `app/src/api/workspaceBackend.js`

---

### 3. SQLAlchemy 模型重复定义冲突

**问题描述**：
```
sqlalchemy.exc.InvalidRequestError: Multiple classes found for path "DBPaperKeyword"
in the registry of this declarative base.
```

**原因**：
- `papers/database.py` 中定义了独立的 `Base` 和模型类
- `models/db_models.py` 中也定义了相同的模型类
- 两个模块都使用统一的 `Base` 导致冲突

**修复方案**：
1. 恢复 `papers/database.py` 使用独立的 `Base`
2. 从 `db_models.py` 中移除论文相关模型
3. 论文模块使用独立的 `papers.db` 数据库文件

**修改文件**：
- `backend/src/papers/database.py`
- `backend/src/models/db_models.py`

---

### 4. SQLite 索引已存在错误

**问题描述**：
```
sqlite3.OperationalError: index ix_files_rel_path already exists
```

**原因**：
- `papers/database.py` 尝试在独立数据库中创建所有表（包括主数据库的表）
- 统一 `Base` 包含所有模型定义，导致表创建冲突

**修复方案**：
- 论文模块使用独立的 `Base` 和模型定义
- 避免与主数据库表产生冲突

**修改文件**：
- `backend/src/papers/database.py`

---

## 修复验证

### 前端修复验证
- [x] 工作区数据损坏自动修复
- [x] `workspaceName` 计算属性类型安全
- [x] API 请求参数验证
- [x] 错误信息正确显示

### 后端修复验证
- [x] Uvicorn 正常启动
- [x] SQLAlchemy 模型无冲突
- [x] 论文模块独立数据库正常初始化
- [x] API 端点正常响应

---

## 技术要点

### 1. Pinia 持久化数据验证
- 应用启动时立即检查并修复损坏数据
- 所有使用持久化数据的地方添加类型验证
- 提供自动修复机制

### 2. SQLAlchemy 多 Base 策略
- 不同功能模块使用独立的 `Base`
- 避免表定义冲突
- 支持独立的数据库文件

### 3. 错误处理最佳实践
- 支持多种错误格式
- 提供友好的错误信息
- 详细的日志记录

---

## 相关文档

- [AGENTS.md](../../AGENTS.md) - AI 代理开发指南
- [2026-04-06-startup-errors-fix.md](./2026-04-06-startup-errors-fix.md) - 项目启动错误修复

---

**修复日期**：2026-04-06  
**修复状态**：✅ 已完成  
**影响版本**：v1.1+
