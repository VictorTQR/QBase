# v1.2 架构准备阶段实施报告

**日期**: 2026-04-05  
**版本**: v1.2-prep  
**状态**: ✅ 已完成

## 概述

本阶段为 QBase v1.2 的新文件管理架构做准备，完成了低风险的基础设施建设，包括清理未使用依赖、创建 .qbase 目录规范、扩展数据库 Schema 以及文件哈希计算工具。

## 完成的任务

### 1. 清理 Dexie.js 依赖 ✅

**目标**: 移除项目中未使用的 Dexie.js 依赖，精简依赖树。

**变更**:
- 从 `app/package.json` 移除 `"dexie": "^4.3.0"`
- 删除 `app/package-lock.json`（将在后续 npm install 时重新生成）

**影响**:
- 项目依赖更加精简
- 减少包体积
- 为后续迁移到 SQLite 做准备

---

### 2. 创建 .qbase/ 目录规范 ✅

**目标**: 建立标准化的工作区元数据目录结构，用于存储生成内容、索引、缓存等。

**新增文件**:
- `backend/src/services/workspace_service.py` - 工作区管理服务
- `backend/src/api/workspace.py` - 工作区 API

**修改文件**:
- `backend/src/config.py` - 添加 .qbase 目录配置
- `backend/main.py` - 注册 workspace 路由

**目录结构**:
```
.qbase/
├── generated/      # AI 生成的派生内容
├── indexes/        # 向量索引等
├── cache/          # 临时缓存
├── config.json     # 工作区配置
├── metadata.db     # 元数据数据库
└── .gitignore      # Git 忽略规则
```

**API 端点**:
- `POST /api/workspace/initialize` - 初始化工作区
- `GET /api/workspace/check-initialized` - 检查工作区状态

---

### 3. 扩展 SQLite Schema ✅

**目标**: 添加新架构所需的数据库表，为文件索引和派生数据管理奠定基础。

**修改文件**:
- `backend/src/models/db_models.py` - 添加新模型

**新增表**:

#### DBFile (文件索引表)
```python
hash: String(16)          # SHA-256 前16位（主键）
rel_path: String          # 相对工作区路径（唯一）
file_type: String(32)     # 文件类型: md | pdf | audio | video
size: Integer             # 文件大小(字节)
mtime: Integer            # 最后修改时间戳
status: String(32)        # 状态: pending | processing | ready | error | missing | orphan
created_at: Integer       # 创建时间戳
updated_at: Integer       # 更新时间戳
```

#### DBDerivative (派生数据表)
```python
id: Integer               # 自增主键
file_hash: String(16)     # 关联文件哈希（外键）
type: String(32)          # 类型: raw_text | transcript | notes | flashcards | mindmap | analysis
version: Integer           # 版本号
model_used: String(255)   # 使用的模型
status: String(32)         # 状态: ready | outdated | error
created_at: Integer        # 创建时间戳
```

#### DBTask (任务队列表)
```python
id: Integer               # 自增主键
file_hash: String(16)     # 关联文件哈希
task_type: String(32)     # 任务类型: parse | embed | generate | sync
status: String(32)        # 状态: queued | running | success | failed
progress: Integer          # 进度 0-100
error_msg: Text            # 错误信息
created_at: Integer        # 创建时间戳
started_at: Integer        # 开始时间戳
completed_at: Integer      # 完成时间戳
```

**新增 Repository**:
- `backend/src/repositories/file_repository.py` - 文件数据访问层
- `backend/src/repositories/derivative_repository.py` - 派生数据访问层

---

### 4. 文件哈希计算工具 ✅

**目标**: 提供基于内容的文件哈希计算能力，支持文件去重和变更检测。

**修改文件**:
- `backend/src/utils/file_hash.py` - 更新为同步版本

**新增文件**:
- `backend/src/api/files.py` - 文件 API

**修改文件**:
- `backend/main.py` - 注册 files 路由

**功能**:
- `compute_file_hash(file_path, length=16)` - 计算文件 SHA-256 哈希
- `compute_short_hash(content, length=16)` - 计算内容短哈希
- 分块读取大文件（64KB 块）
- 默认返回前 16 位哈希

**API 端点**:
- `POST /api/files/hash` - 计算文件哈希

---

## 文件清单

### 修改的文件
| 文件 | 说明 |
|------|------|
| `app/package.json` | 移除 dexie 依赖 |
| `backend/src/config.py` | 添加 .qbase 目录配置 |
| `backend/src/models/db_models.py` | 添加新架构表 |
| `backend/src/utils/file_hash.py` | 更新哈希工具 |
| `backend/main.py` | 注册新路由 |

### 新增的文件
| 文件 | 说明 |
|------|------|
| `backend/src/services/workspace_service.py` | 工作区管理服务 |
| `backend/src/api/workspace.py` | 工作区 API |
| `backend/src/repositories/file_repository.py` | 文件 Repository |
| `backend/src/repositories/derivative_repository.py` | 派生数据 Repository |
| `backend/src/api/files.py` | 文件 API |

---

## 技术亮点

1. **渐进式迁移**: 本次变更仅添加基础设施，不影响现有功能
2. **向后兼容**: 现有 ParseTask 等表保持不变
3. **内容哈希**: 基于 SHA-256 的文件追踪，支持去重和变更检测
4. **标准化目录**: .qbase 目录结构为后续功能提供统一存储位置
5. **Repository 模式**: 数据访问层抽象，便于测试和维护

---

## 后续规划

本阶段为 v1.2 的完整架构迁移奠定了基础，后续将包括：

1. **文件扫描器**: 自动扫描工作区文件并构建索引
2. **前端集成**: 将新架构与现有工作区管理集成
3. **迁移工具**: 将现有解析数据迁移到新 Schema
4. **实时同步**: 文件变更监听和自动更新

---

## 相关文档

- [实施计划](../plans/2026-04-05-qbase-architecture-prep.md)
- [新文件管理架构设计方案参考](../use%20for%20reference/新文件管理架构设计方案参考.md)
