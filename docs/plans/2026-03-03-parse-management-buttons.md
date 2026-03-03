# 解析管理禁用按钮功能实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现解析管理页面 4 个被禁用按钮的完整功能：清除已完成、清空队列、批量解析待处理文件、重试失败文件

**Architecture:** 采用自底向上的实现方式：后端 Repository → 后端 TaskManager → 后端 API → 前端 API → 前端 Store → 前端组件

**Tech Stack:** FastAPI (后端), SQLAlchemy (ORM), Vue 3 + Pinia (前端), Element Plus (UI)

---

## 功能清单

| 功能 | 前端组件 | 后端 API |
|------|---------|---------|
| 清除已完成 | ParseQueueView.vue | DELETE /api/mineru/tasks/clear-completed |
| 清空队列 | ParseQueueView.vue | DELETE /api/mineru/tasks/clear-all |
| 批量解析待处理文件 | ParseStatsView.vue | POST /api/mineru/tasks/batch-parse-pending |
| 重试失败文件 | ParseStatsView.vue | POST /api/mineru/tasks/retry-failed |

---

## Task 1: 后端 Repository 层 - 添加删除和批量查询方法

**Files:**
- Modify: `E:\Code\workSpace\GitBank\QBase\backend\src\repositories\parse_task_repository.py`

**Step 1: 添加 Repository 方法**

在 `ParseTaskRepository` 类中添加以下方法：

```python
async def delete_by_states(self, states: List[str]) -> int:
    """按状态删除任务"""
    from sqlalchemy import delete
    result = await self.db.execute(
        delete(ParseTask).where(ParseTask.state.in_(states))
    )
    await self.db.commit()
    count = result.rowcount
    logger.info(f"删除了 {count} 个任务 (states: {states})")
    return count

async def delete_all(self) -> int:
    """删除所有任务"""
    from sqlalchemy import delete
    result = await self.db.execute(delete(ParseTask))
    await self.db.commit()
    count = result.rowcount
    logger.info(f"删除了所有 {count} 个任务")
    return count
```

**Step 2: 验证文件结构**

确保这些方法添加在 `get_stats` 方法之后，类定义结束之前。

---

## Task 2: 后端 TaskManager 层 - 添加业务逻辑方法

**Files:**
- Modify: `E:\Code\workSpace\GitBank\QBase\backend\src\mineru\task_manager.py`

**Step 1: 添加 TaskManager 方法**

在 `TaskManager` 类中添加以下方法（放在 `get_stats` 之后，`_task_to_dict` 之前）：

```python
async def clear_completed(self) -> int:
    """清除已完成的任务"""
    repo, session = await self._get_repo()
    try:
        return await repo.delete_by_states(["done"])
    finally:
        await session.close()

async def clear_all(self) -> int:
    """清空所有任务"""
    repo, session = await self._get_repo()
    try:
        return await repo.delete_all()
    finally:
        await session.close()

async def batch_parse_pending(self, background_tasks) -> int:
    """批量解析待处理文件"""
    repo, session = await self._get_repo()
    try:
        pending_tasks = await repo.list_by_state("pending", limit=100)
        count = 0
        for task in pending_tasks:
            task_dict = self._task_to_dict(task)
            background_tasks.add_task(self.poll_task_status, task_dict["id"])
            count += 1
        logger.info(f"批量启动了 {count} 个待解析任务")
        return count
    finally:
        await session.close()

async def retry_failed(self, background_tasks) -> int:
    """重试失败的任务"""
    repo, session = await self._get_repo()
    try:
        failed_tasks = await repo.list_by_state("failed", limit=100)
        count = 0
        for task in failed_tasks:
            # 重置任务状态为 pending
            await repo.update(task.id, {
                "state": "pending",
                "error_msg": None,
                "updated_at": datetime.now().isoformat()
            })
            task_dict = self._task_to_dict(task)
            background_tasks.add_task(self.poll_task_status, task_dict["id"])
            count += 1
        logger.info(f"重试了 {count} 个失败任务")
        return count
    finally:
        await session.close()
```

**Step 2: 导出这些方法**

确保这些方法是 `TaskManager` 类的公共方法。

---

## Task 3: 后端 API 层 - 添加 4 个新端点

**Files:**
- Modify: `E:\Code\workSpace\GitBank\QBase\backend\src\api\mineru.py`

**Step 1: 添加新的 Schema（如需要）**

在文件开头添加简单的响应模型（如果还没有的话）：

```python
class OperationResponse(BaseModel):
    success: bool
    count: int
    message: str
```

**Step 2: 添加 4 个 API 端点**

在文件末尾（`download_zip` 函数之后）添加：

```python
@router.delete("/tasks/clear-completed", response_model=OperationResponse)
async def clear_completed_tasks():
    """清除已完成的任务"""
    try:
        count = await task_manager.clear_completed()
        return OperationResponse(
            success=True,
            count=count,
            message=f"已清除 {count} 个已完成任务"
        )
    except Exception as e:
        logger.error(f"清除已完成任务失败: {str(e)}")
        raise HTTPException(status_code=500 detail=str(e))

@router.delete("/tasks/clear-all", response_model=OperationResponse)
async def clear_all_tasks():
    """清空所有任务"""
    try:
        count = await task_manager.clear_all()
        return OperationResponse(
            success=True,
            count=count,
            message=f"已清空 {count} 个任务"
        )
    except Exception as e:
        logger.error(f"清空任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tasks/batch-parse-pending", response_model=OperationResponse)
async def batch_parse_pending(background_tasks: BackgroundTasks):
    """批量解析待处理文件"""
    try:
        count = await task_manager.batch_parse_pending(background_tasks)
        return OperationResponse(
            success=True,
            count=count,
            message=f"已启动 {count} 个待解析任务"
        )
    except Exception as e:
        logger.error(f"批量解析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tasks/retry-failed", response_model=OperationResponse)
async def retry_failed_tasks(background_tasks: BackgroundTasks):
    """重试失败的任务"""
    try:
        count = await task_manager.retry_failed(background_tasks)
        return OperationResponse(
            success=True,
            count=count,
            message=f"已重试 {count} 个失败任务"
        )
    except Exception as e:
        logger.error(f"重试失败任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 3: 检查导入**

确保 `OperationResponse` 被正确导入或定义。如果 `models.schemas` 中没有，就在本文件中定义。

---

## Task 4: 前端 API 层 - 添加 API 调用方法

**Files:**
- Modify: `E:\Code\workSpace\GitBank\QBase\app\src\api\parseBackend.js`

**Step 1: 添加 4 个 API 方法**

在 `ParseBackendApi` 类中添加：

```javascript
static async clearCompleted() {
  const request = backend.client.delete('/api/mineru/tasks/clear-completed')
  return await request.json()
}

static async clearAll() {
  const request = backend.client.delete('/api/mineru/tasks/clear-all')
  return await request.json()
}

static async batchParsePending() {
  const request = backend.client.post('/api/mineru/tasks/batch-parse-pending')
  return await request.json()
}

static async retryFailed() {
  const request = backend.client.post('/api/mineru/tasks/retry-failed')
  return await request.json()
}
```

---

## Task 5: 前端 Store 层 - 添加 Store 方法

**Files:**
- Modify: `E:\Code\workSpace\GitBank\QBase\app\src\stores\parse.js`

**Step 1: 添加 4 个 Store 方法**

在 `useParseStore` 中添加（放在 `clearError` 之前）：

```javascript
async function clearCompletedTasks() {
  isLoading.value = true
  error.value = null
  try {
    const response = await ParseBackendApi.clearCompleted()
    await fetchTasks()
    await fetchStats()
    return response
  } catch (err) {
    error.value = err.message
    throw err
  } finally {
    isLoading.value = false
  }
}

async function clearAllTasks() {
  isLoading.value = true
  error.value = null
  try {
    const response = await ParseBackendApi.clearAll()
    await fetchTasks()
    await fetchStats()
    return response
  } catch (err) {
    error.value = err.message
    throw err
  } finally {
    isLoading.value = false
  }
}

async function batchParsePending() {
  isLoading.value = true
  error.value = null
  try {
    const response = await ParseBackendApi.batchParsePending()
    await fetchTasks()
    await fetchStats()
    return response
  } catch (err) {
    error.value = err.message
    throw err
  } finally {
    isLoading.value = false
  }
}

async function retryFailedTasks() {
  isLoading.value = true
  error.value = null
  try {
    const response = await ParseBackendApi.retryFailed()
    await fetchTasks()
    await fetchStats()
    return response
  } catch (err) {
    error.value = err.message
    throw err
  } finally {
    isLoading.value = false
  }
}
```

**Step 2: 在 return 对象中导出这些方法**

在 `return` 语句中添加：

```javascript
clearCompletedTasks,
clearAllTasks,
batchParsePending,
retryFailedTasks,
```

确保它们在 `clearError` 之前。

---

## Task 6: 前端组件 - ParseQueueView.vue 启用按钮

**Files:**
- Modify: `E:\Code\workSpace\GitBank\QBase\app\src\components\parse\ParseQueueView.vue`

**Step 1: 添加处理函数和 loading 状态**

在 `<script setup>` 中添加：

```javascript
import { ref, computed } from 'vue'
import { useParseStore } from '@/stores/parse'
import { ElMessage, ElMessageBox } from 'element-plus'

const parseStore = useParseStore()
const activeQueueTab = ref('running')
const isClearingCompleted = ref(false)
const isClearingAll = ref(false)

const pendingTasks = computed(() => parseStore.pendingTasks)
const runningTasks = computed(() => parseStore.runningTasks)
const failedTasks = computed(() => parseStore.failedTasks)
const doneTasks = computed(() => parseStore.doneTasks)

const handleClearCompleted = async () => {
  if (doneTasks.value.length === 0) {
    ElMessage.warning('没有已完成的任务可清除')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要清除 ${doneTasks.value.length} 个已完成的任务吗？`,
      '确认清除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    isClearingCompleted.value = true
    const response = await parseStore.clearCompletedTasks()
    ElMessage.success(response.message)
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(err.message || '清除失败')
    }
  } finally {
    isClearingCompleted.value = false
  }
}

const handleClearAll = async () => {
  if (parseStore.tasks.length === 0) {
    ElMessage.warning('队列已经是空的')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      '确定要清空所有任务吗？此操作不可恢复！',
      '确认清空',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'error'
      }
    )
    
    isClearingAll.value = true
    const response = await parseStore.clearAllTasks()
    ElMessage.success(response.message)
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(err.message || '清空失败')
    }
  } finally {
    isClearingAll.value = false
  }
}
```

**Step 2: 更新模板中的按钮**

替换按钮部分：

```vue
<div class="header-actions">
  <el-button 
    size="small" 
    :disabled="doneTasks.length === 0 || isClearingCompleted"
    :loading="isClearingCompleted"
    @click="handleClearCompleted"
  >
    清除已完成
  </el-button>
  <el-button 
    size="small" 
    type="danger" 
    :disabled="parseStore.tasks.length === 0 || isClearingAll"
    :loading="isClearingAll"
    @click="handleClearAll"
  >
    清空队列
  </el-button>
</div>
```

---

## Task 7: 前端组件 - ParseStatsView.vue 启用按钮

**Files:**
- Modify: `E:\Code\workSpace\GitBank\QBase\app\src\components\parse\ParseStatsView.vue`

**Step 1: 添加处理函数和 loading 状态**

在 `<script setup>` 中添加：

```javascript
import { computed } from 'vue'
import { Document, CircleCheck, Clock, CircleClose } from '@element-plus/icons-vue'
import { useParseStore } from '@/stores/parse'
import { ElMessage } from 'element-plus'

const parseStore = useParseStore()
const isBatchParsing = ref(false)
const isRetrying = ref(false)

const stats = computed(() => parseStore.stats)
const pendingTasks = computed(() => parseStore.pendingTasks)

const handleBatchParse = async () => {
  if (stats.value.pending === 0) {
    ElMessage.warning('没有待解析的文件')
    return
  }
  
  try {
    isBatchParsing.value = true
    const response = await parseStore.batchParsePending()
    ElMessage.success(response.message)
  } catch (err) {
    ElMessage.error(err.message || '批量解析失败')
  } finally {
    isBatchParsing.value = false
  }
}

const handleRetryFailed = async () => {
  if (stats.value.failed === 0) {
    ElMessage.warning('没有失败的文件')
    return
  }
  
  try {
    isRetrying.value = true
    const response = await parseStore.retryFailedTasks()
    ElMessage.success(response.message)
  } catch (err) {
    ElMessage.error(err.message || '重试失败')
  } finally {
    isRetrying.value = false
  }
}
```

**Step 2: 更新模板中的按钮**

替换快速操作部分的按钮：

```vue
<div class="quick-actions">
  <el-button 
    type="primary" 
    :disabled="stats.pending === 0 || isBatchParsing"
    :loading="isBatchParsing"
    @click="handleBatchParse"
  >
    批量解析待处理文件
  </el-button>
  <el-button 
    type="warning" 
    :disabled="stats.failed === 0 || isRetrying"
    :loading="isRetrying"
    @click="handleRetryFailed"
  >
    重试失败文件
  </el-button>
</div>
```

---

## Task 8: 测试验证

**测试步骤：**

1. 启动后端服务：`cd backend && python -m src.main`
2. 启动前端开发服务器：`cd app && npm run dev`
3. 启动 Electron：`cd app && npm run ele`（或完整启动 `npm run start`）
4. 进入解析管理页面
5. 测试每个按钮：
   - 先添加一些测试文件到解析队列
   - 测试"批量解析待处理文件"
   - 等待一些完成后，测试"清除已完成"
   - 制造一些失败任务，测试"重试失败文件"
   - 最后测试"清空队列"（注意备份数据）

**预期结果：**
- 所有按钮不再显示"开发中"
- 按钮根据状态正确禁用/启用
- 点击后有 loading 状态
- 操作成功/失败有消息提示
- 危险操作有二次确认
- 数据正确刷新

---

## 总结

本计划实现了解析管理页面 4 个禁用按钮的完整功能，涵盖了从后端数据库到前端 UI 的全链路实现。每个任务都可以独立进行测试和验证。
