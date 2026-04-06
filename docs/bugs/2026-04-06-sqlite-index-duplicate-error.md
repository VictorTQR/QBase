# SQLite 数据库索引重复创建问题修复记录

## 问题描述

应用启动时调用 `/api/workspace/scan` 接口报错：

```
(sqlite3.OperationalError) index ix_files_status already exists
[SQL: CREATE INDEX ix_files_status ON files (status)]
```

错误会依次出现在不同索引上：`ix_parse_tasks_id`、`ix_files_rel_path`、`ix_files_status` 等。

## 环境信息

- **项目**: QBase - 本地知识库管理系统
- **后端**: FastAPI + SQLAlchemy 2.0 + aiosqlite
- **数据库**: SQLite
- **问题发生时机**: 应用启动时初始化数据库、工作区扫描时

## 根本原因分析

这个问题在 `SQLAlchemy 2.0 + SQLite` 组合中非常典型：

1. **SQLite 原生不支持 `CREATE INDEX` 的自动幂等检查**
2. **SQLAlchemy 的 `checkfirst=True` 在 SQLite 方言中对索引的探测存在已知缺陷**，导致即使索引已存在，仍会执行 `CREATE INDEX` 并抛出 `OperationalError`
3. **模型配置不一致**：部分模型有 `extend_existing=True`，部分没有，导致元数据合并逻辑不一致
4. **模块重复导入**：`db_models.py` 被多次导入（如 `database.py`、`file_scanner.py`、`workspace.py` 同时导入），导致元数据重复注册

## 解决方案

### 1. 统一模型配置

**文件**: `backend/src/models/db_models.py`

所有模型统一添加 `extend_existing=True`：

```python
class ParseTask(Base):
    __tablename__ = "parse_tasks"
    __table_args__ = {"extend_existing": True}  # 必须加

    id = Column(String, primary_key=True, index=True)
    # ... 其他字段

class DBFile(Base):
    __tablename__ = "files"
    __table_args__ = {"extend_existing": True}  # 必须加

    hash = Column(String(16), primary_key=True, index=True)
    # ... 其他字段

# 其他模型同理...
```

> **重要**：要么所有表都加 `extend_existing=True`，要么都不加。混用会导致元数据合并逻辑错乱。

### 2. 修复数据库初始化逻辑

**文件**: `backend/src/services/database_service.py`

```python
@classmethod
async def init_workspace_db(cls, workspace_path: str):
    """初始化工作区数据库，兼容元数据重复注册场景"""
    from sqlalchemy import text
    from src.models.db_models import Base

    engine = cls.get_engine(workspace_path)

    def _safe_init(sync_conn):
        """安全初始化：捕获元数据冲突 + 索引冲突"""
        try:
            # 首选：标准幂等创建
            Base.metadata.create_all(sync_conn, checkfirst=True)
        except Exception as e:
            err = str(e).lower()

            # 情况1: 元数据重复注册 -> 跳过（表已定义，无需处理）
            if "already defined for this metadata" in err:
                logger.debug("MetaData already registered, skipping table definition")
                return

            # 情况2: 索引/表已存在 -> 降级逐表处理
            if "already exists" in err:
                logger.debug("Object exists, falling back to per-table creation")
                for table in Base.metadata.sorted_tables:
                    try:
                        table.create(sync_conn, checkfirst=True)
                    except Exception as e2:
                        if "already exists" in str(e2).lower():
                            logger.debug(f"Skip existing: {table.name}")
                        else:
                            raise
            else:
                # 其他未知错误，原样抛出
                raise

    async with engine.begin() as conn:
        await conn.run_sync(_safe_init)

    logger.info(f"Workspace database ready: {workspace_path}")
```

### 3. 同步修改其他文件

同样的逻辑应用到：
- `backend/src/database.py` - 主数据库初始化
- `backend/src/papers/database.py` - 论文数据库模块

## 为什么这个方案有效？

| 之前的尝试 | 失败原因 | 本方案如何解决 |
|:---|:---|:---|
| `inspector.get_table_names()` + 手动建表 | 只检查了表，没处理索引 | 统一交由 `Base.metadata.create_all` 处理，异常时降级逐表处理 |
| 查 `sqlite_master` 后 `DROP INDEX` | `aiosqlite` 事务中 `DROP` 和 `CREATE` 可能不在同一原子上下文 | 放弃手动 `DROP`，直接捕获 `already exists` 异常并跳过 |
| `checkfirst=True` | SQLAlchemy 2.0 的 SQLite 方言对索引的 `checkfirst` 探测不完整 | 用 `try...except` 作为兜底，不依赖方言探测 |
| 移除 `extend_existing=True` | 导致 `Table 'xxx' is already defined for this MetaData instance` 错误 | 统一添加 `extend_existing=True` |

## 验证步骤

1. 删除所有工作区目录下的 `.qbase/metadata.db` 文件
2. **不使用 `--reload`** 启动后端：
   ```bash
   cd backend
   uvicorn main:app --host 127.0.0.1 --port 8000
   ```
3. 访问应用，观察日志：
   - ✅ 应看到 `Workspace database ready`
   - ❌ 无 `InvalidRequestError` 或 `OperationalError`

## 长期建议

| 问题 | 建议方案 |
|------|----------|
| 元数据管理混乱 | 引入 `Alembic` 做迁移管理，避免 `create_all` |
| 开发环境热重载 | 使用 `--reload-include` 限制监控文件，或改用 `watchfiles` |
| 多进程/线程初始化 | 加文件锁或单例锁，避免并发写 `.db` 文件 |
| 模型导入循环 | 用 `TYPE_CHECKING` + 字符串注解延迟导入 |

## 相关文件

- `backend/src/models/db_models.py`
- `backend/src/database.py`
- `backend/src/services/database_service.py`
- `backend/src/papers/database.py`
