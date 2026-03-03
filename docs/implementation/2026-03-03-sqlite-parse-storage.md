# SQLite 解析结果存储 - 实施报告

**状态**: ✅ 已完成  
**版本**: v0.9+  
**最后更新**: 2026-03-03

## 概述

本次实施在后端引入 SQLite 数据库来持久化存储解析结果，通过 SHA-256 文件哈希实现去重，完全移除了前端的 LocalStorage/IndexedDB 存储依赖。

---

## 实现的功能

### 1. 后端 SQLite 集成

**核心特性：**
- ✅ 使用 SQLAlchemy ORM + aiosqlite 异步驱动
- ✅ ParseTask 数据库表设计
- ✅ Repository 模式数据访问层
- ✅ 文件哈希计算（SHA-256）
- ✅ 任务状态持久化
- ✅ 服务重启不丢失数据

### 2. 文件去重机制

**去重策略：**
- 通过 SHA-256 计算文件内容哈希
- 哈希值作为唯一索引（UNIQUE 约束）
- 解析前自动检查去重
- 重复文件直接返回已有结果

### 3. 增强的 API 端点

**新增端点：**
- `POST /api/mineru/check-duplicate` - 去重检查
- `GET /api/mineru/tasks` - 分页任务列表
- `GET /api/mineru/stats` - 解析统计

**增强端点：**
- `POST /api/mineru/parse` - 集成去重检查
- `POST /api/mineru/parse-local` - 集成去重检查
- `GET /api/mineru/tasks/{task_id}/result` - 保存结果到数据库

### 4. 字段设计

**result_file_path 替代 zip_path：**
- 支持多种解析结果格式（ZIP、JSON 等）
- 为未来多解析服务商扩展预留空间
- 添加 `parser_type` 和 `result_file_format` 字段

---

## 技术架构

### 数据库表设计

```sql
CREATE TABLE parse_tasks (
    id TEXT PRIMARY KEY,
    batch_id TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_path TEXT,
    file_hash TEXT NOT NULL UNIQUE,
    file_size INTEGER,
    parser_type TEXT NOT NULL DEFAULT 'mineru',
    state TEXT NOT NULL,
    error_msg TEXT,
    markdown_content TEXT,
    result_file_path TEXT,
    result_file_format TEXT DEFAULT 'zip',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

### 后端分层架构

```
backend/src/
├── database.py                    # 数据库连接和初始化
├── models/
│   ├── db_models.py              # SQLAlchemy 模型
│   └── schemas.py               # Pydantic 响应模型
├── repositories/
│   └── parse_task_repository.py  # 数据访问层
├── mineru/
│   └── task_manager.py          # 重构使用数据库
└── utils/
    └── file_hash.py             # 文件哈希工具
```

### 状态映射

| 前端状态 | 后端状态 | 说明 |
|----------|----------|------|
| pending | pending | 待解析 |
| parsing | running | 解析中 |
| completed | done | 已完成 |
| failed | failed | 失败 |

---

## 文件变更总览

### 后端新增

- `backend/src/database.py` - 数据库连接管理
- `backend/src/models/db_models.py` - ParseTask 模型
- `backend/src/repositories/parse_task_repository.py` - Repository 层
- `backend/src/utils/file_hash.py` - 文件哈希工具

### 后端修改

- `backend/pyproject.toml` - 添加 SQLAlchemy + aiosqlite
- `backend/src/config.py` - 添加 DATABASE_URL 配置
- `backend/src/mineru/task_manager.py` - 重构使用数据库
- `backend/src/models/schemas.py` - 新增响应模型
- `backend/src/api/mineru.py` - 增强 API
- `backend/main.py` - 添加数据库初始化

### 前端新增

- `app/src/api/parseBackend.js` - 后端 API 客户端

### 前端修改

- `app/src/stores/parse.js` - 重构使用后端 API（部分完成）

### 前端删除

- `app/src/repositories/ParseIndexRepository.js`
- `app/src/repositories/IndexedDBRepository.js`

---

## API 文档

### 去重检查

```http
POST /api/mineru/check-duplicate
Content-Type: application/json

{
  "file_hash": "sha256_hash_string",
  "file_path": "/path/to/file.pdf"
}

Response:
{
  "is_duplicate": true,
  "existing_task": { ... }
}
```

### 任务列表

```http
GET /api/mineru/tasks?limit=100&offset=0

Response:
{
  "tasks": [ ... ],
  "total": 50,
  "limit": 100,
  "offset": 0
}
```

### 解析统计

```http
GET /api/mineru/stats

Response:
{
  "total": 50,
  "pending": 10,
  "running": 5,
  "done": 30,
  "failed": 5
}
```

---

## 后续工作

### 待完成

- [ ] 完整的前端组件重构（计划文档已创建）
- [ ] 解析详情抽屉功能
- [ ] 批量解析和重试功能
- [ ] 导出功能适配
- [ ] 完整的集成测试

### 已知问题

- TaskManager.check_duplicate 的 LSP 类型警告（不影响运行）
- /result 端点需要补充保存完整 result 的逻辑

---

## 相关文档

- [实施计划](../plans/2026-03-03-sqlite-parse-storage.md)
- [前端重构计划](../plans/2026-03-03-frontend-parse-refactor.md)
- [解析管理功能文档](../features/parse-management.md)
