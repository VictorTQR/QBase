# 后端严重问题修复实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 修复后端代码审查中发现的两个严重问题：1) vector.py 的数据库会话管理 bug；2) 移除 sys.path.insert 反模式，改用正确的导入方式

**Architecture:** 保持现有分层架构（API → Service → Repository → Model），仅修复导入方式和会话管理问题，不改动业务逻辑

**Tech Stack:** FastAPI, SQLAlchemy 2.0 (async), Python 3.12

---

## 前置检查

**检查当前工作目录:**
```bash
cd f:\Code\00Code\GitBank\QBase
pwd
```
Expected: `f:\Code\00Code\GitBank\QBase`

**检查 Python 环境:**
```bash
cd backend
python --version
```
Expected: Python 3.12+

---

## Task 1: 修复 vector.py 的数据库会话管理 bug

**问题描述:**
第 45 行 `repo, session = AsyncSessionLocal(), None` 是错误的，因为 `AsyncSessionLocal()` 返回的是 session 对象，不是元组。这会导致后续代码出错。

**Files:**
- Modify: `backend/src/api/vector.py:45-70`

**Step 1: 查看当前问题代码**

读取文件确认问题:
```bash
cd f:\Code\00Code\GitBank\QBase\backend
head -80 src/api/vector.py
```
Expected: 显示第 45 行有 `repo, session = AsyncSessionLocal(), None`

**Step 2: 修复会话管理代码**

修改 `backend/src/api/vector.py` 第 45-70 行:

原代码:
```python
        # 降级：从 task_id 获取
        if not content and validated_request.task_id:
            logger.info(
                f"[Vector API] 从数据库获取内容，task_id: {validated_request.task_id}"
            )
            repo, session = AsyncSessionLocal(), None  # ❌ 错误
            try:
                session = AsyncSessionLocal()  # ❌ 重复创建
                repo = ParseTaskRepository(session)
                task = await repo.get_by_id(validated_request.task_id)
                if task and task.markdown_content:
                    content = task.markdown_content
                    logger.info(
                        f"[Vector API] 从数据库获取内容成功，长度: {len(content)}"
                    )
                else:
                    logger.warning(
                        f"[Vector API] 无法从数据库获取内容，task_id: {validated_request.task_id}"
                    )
            except Exception as e:
                logger.error(f"[Vector API] 从数据库获取内容失败: {e}")
            finally:
                if session:
                    await session.close()
```

修复为:
```python
        # 降级：从 task_id 获取
        if not content and validated_request.task_id:
            logger.info(
                f"[Vector API] 从数据库获取内容，task_id: {validated_request.task_id}"
            )
            session = AsyncSessionLocal()
            try:
                repo = ParseTaskRepository(session)
                task = await repo.get_by_id(validated_request.task_id)
                if task and task.markdown_content:
                    content = task.markdown_content
                    logger.info(
                        f"[Vector API] 从数据库获取内容成功，长度: {len(content)}"
                    )
                else:
                    logger.warning(
                        f"[Vector API] 无法从数据库获取内容，task_id: {validated_request.task_id}"
                    )
            except Exception as e:
                logger.error(f"[Vector API] 从数据库获取内容失败: {e}")
            finally:
                await session.close()
```

**Step 3: 验证修复**

检查修复后的代码:
```bash
cd f:\Code\00Code\GitBank\QBase\backend
sed -n '45,70p' src/api/vector.py
```
Expected: 显示修复后的代码，没有 `repo, session = AsyncSessionLocal(), None`

**Step 4: Commit**

```bash
cd f:\Code\00Code\GitBank\QBase
git add backend/src/api/vector.py
git commit -m "fix: 修复 vector.py 数据库会话管理 bug

- 移除错误的元组解包语法
- 修复重复创建 session 的问题
- 确保 session 正确关闭"
```

---

## Task 2: 修复 mineru.py 的导入问题

**问题描述:**
使用 `sys.path.insert` 修改运行时路径是反模式，应该使用相对导入。

**Files:**
- Modify: `backend/src/api/mineru.py:1-15`

**Step 1: 查看当前导入代码**

```bash
cd f:\Code\00Code\GitBank\QBase\backend
head -20 src/api/mineru.py
```
Expected: 显示 `sys.path.insert(0, str(Path(__file__).parent.parent))`

**Step 2: 移除 sys.path.insert，改用相对导入**

修改 `backend/src/api/mineru.py`:

原代码 (第 1-15 行):
```python
import os
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.responses import Response
from pydantic import BaseModel
from loguru import logger
import aiofiles
from sqlalchemy.ext.asyncio import AsyncSession

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from src.mineru.task_manager import task_manager
```

修复为:
```python
import os
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.responses import Response
from pydantic import BaseModel
from loguru import logger
import aiofiles
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..mineru.task_manager import task_manager
```

**Step 3: 验证导入修复**

```bash
cd f:\Code\00Code\GitBank\QBase\backend
head -15 src/api/mineru.py
```
Expected: 没有 `sys.path.insert`，使用 `from ..config import settings`

**Step 4: Commit**

```bash
cd f:\Code\00Code\GitBank\QBase
git add backend/src/api/mineru.py
git commit -m "refactor: 移除 mineru.py 的 sys.path.insert 反模式

- 使用相对导入替代运行时路径修改
- 符合 Python 包导入规范"
```

---

## Task 3: 修复 audio/task_manager.py 的导入问题

**Files:**
- Modify: `backend/src/audio/task_manager.py:1-10`

**Step 1: 查看当前导入代码**

```bash
cd f:\Code\00Code\GitBank\QBase\backend
head -15 src/audio/task_manager.py
```
Expected: 显示 `sys.path.insert(0, str(Path(__file__).parent.parent))`

**Step 2: 移除 sys.path.insert，改用相对导入**

修改 `backend/src/audio/task_manager.py`:

原代码 (第 1-10 行):
```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from typing import Dict, Optional
from loguru import logger
from datetime import datetime

from database import AsyncSessionLocal
from repositories.parse_task_repository import ParseTaskRepository
```

修复为:
```python
import asyncio
from typing import Dict, Optional
from loguru import logger
from datetime import datetime

from ..database import AsyncSessionLocal
from ..repositories.parse_task_repository import ParseTaskRepository
```

**Step 3: 验证导入修复**

```bash
cd f:\Code\00Code\GitBank\QBase\backend
head -15 src/audio/task_manager.py
```
Expected: 没有 `sys.path.insert`，使用 `from ..database import`

**Step 4: Commit**

```bash
cd f:\Code\00Code\GitBank\QBase
git add backend/src/audio/task_manager.py
git commit -m "refactor: 移除 audio/task_manager.py 的 sys.path.insert

- 使用相对导入替代运行时路径修改"
```

---

## Task 4: 修复 audio.py 的导入问题

**Files:**
- Modify: `backend/src/api/audio.py`

**Step 1: 查看当前导入代码**

```bash
cd f:\Code\00Code\GitBank\QBase\backend
head -20 src/api/audio.py
```

**Step 2: 如果存在 sys.path.insert，则修复**

如果有 `sys.path.insert`，则替换为相对导入:
```python
# 从
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.xxx import yyy

# 改为
from ..xxx import yyy
```

**Step 3: Commit (如果有修改)**

```bash
cd f:\Code\00Code\GitBank\QBase
git add backend/src/api/audio.py
git commit -m "refactor: 移除 audio.py 的 sys.path.insert"
```

---

## Task 5: 修复 vector/__init__.py 的导入问题

**Files:**
- Modify: `backend/src/vector/__init__.py`

**Step 1: 查看当前导入代码**

```bash
cd f:\Code\00Code\GitBank\QBase\backend
cat src/vector/__init__.py
```

**Step 2: 如果存在 sys.path.insert，则修复**

**Step 3: Commit (如果有修改)**

---

## Task 6: 验证所有修复

**Step 1: 检查是否还有剩余的 sys.path.insert**

```bash
cd f:\Code\00Code\GitBank\QBase\backend
grep -r "sys.path.insert" src/
```
Expected: 无输出（表示已全部修复）

**Step 2: 语法检查**

```bash
cd f:\Code\00Code\GitBank\QBase\backend
python -m py_compile src/api/vector.py
python -m py_compile src/api/mineru.py
python -m py_compile src/audio/task_manager.py
```
Expected: 无错误输出

**Step 3: 尝试启动后端验证**

```bash
cd f:\Code\00Code\GitBank\QBase\backend
python -c "from src.api.vector import router; print('vector.py OK')"
python -c "from src.api.mineru import router; print('mineru.py OK')"
python -c "from src.audio.task_manager import AudioTaskManager; print('task_manager.py OK')"
```
Expected: 全部显示 OK

---

## Task 7: 最终验证和提交

**Step 1: 查看所有变更**

```bash
cd f:\Code\00Code\GitBank\QBase
git status
git diff --stat
```

**Step 2: 运行后端启动测试**

```bash
cd f:\Code\00Code\GitBank\QBase\backend
python -c "
import sys
sys.path.insert(0, 'src')
from main import app
print('FastAPI app 加载成功')
print('路由列表:')
for route in app.routes:
    if hasattr(route, 'methods'):
        print(f'  {route.methods} {route.path}')
"
```
Expected: 显示所有路由，无导入错误

**Step 3: 最终 Commit**

```bash
cd f:\Code\00Code\GitBank\QBase
git log --oneline -5
```
Expected: 显示所有修复提交

---

## 修复清单总结

| 文件 | 问题 | 修复方式 |
|------|------|----------|
| `src/api/vector.py` | 会话管理 bug | 修复变量赋值和重复创建 |
| `src/api/mineru.py` | sys.path.insert | 改用相对导入 `from ..config` |
| `src/audio/task_manager.py` | sys.path.insert | 改用相对导入 `from ..database` |
| `src/api/audio.py` | 如有问题 | 同上 |
| `src/vector/__init__.py` | 如有问题 | 同上 |

---

## 测试验证点

1. **vector.py 修复验证:**
   - 代码语法正确
   - 能正确创建和关闭数据库会话
   - 从 task_id 获取内容功能正常

2. **导入修复验证:**
   - 所有文件无 `sys.path.insert`
   - 相对导入语法正确
   - 模块能正常导入

3. **整体验证:**
   - FastAPI app 能正常启动
   - 所有路由正常注册
   - 无导入错误
