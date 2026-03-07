# 向量索引管理标签页 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在解析管理页面添加标签页切换功能，同时显示"解析任务"和"向量索引"，让用户能够查看和管理所有已索引的文件（包括 Markdown）

**Architecture:** 
1. 后端新增 API 端点获取已索引文件列表
2. 前端 vector store 新增加载已索引文件的方法
3. ParseDocumentsView.vue 添加标签页组件，第二个标签页显示向量索引管理界面

**Tech Stack:** FastAPI, LanceDB, Vue 3, Pinia, Element Plus

---

## Task 1: 后端 - 在 lancedb_service.py 中添加 list_indexed_files 方法

**Files:**
- Modify: `backend/src/vector/lancedb_service.py`

**Step 1: 添加导入（如需要）**

检查文件顶部，确保已有必要的导入。

**Step 2: 在 LanceDBService 类中添加 list_indexed_files 方法**

在 `get_stats` 方法之后添加：

```python
@classmethod
def list_indexed_files(cls) -> List[Dict[str, Any]]:
    """获取所有已索引的文件列表（按文件分组）"""
    if cls._table is None:
        return []
    
    # 获取所有数据
    all_chunks = cls._table.to_pandas()
    
    if all_chunks.empty:
        return []
    
    # 按 file_path 分组
    grouped = all_chunks.groupby('file_path')
    
    indexed_files = []
    for file_path, group in grouped:
        # 获取该文件的信息
        first_chunk = group.iloc[0]
        latest_chunk = group.iloc[-1]
        
        indexed_files.append({
            "file_path": file_path,
            "file_name": first_chunk['file_name'],
            "workspace_id": first_chunk['workspace_id'],
            "created_at": int(latest_chunk['created_at']),
            "chunk_count": len(group),
        })
    
    # 按 created_at 降序排序
    indexed_files.sort(key=lambda x: x['created_at'], reverse=True)
    
    return indexed_files
```

**Step 3: 验证代码语法**

检查代码是否有语法错误。

---

## Task 2: 后端 - 在 vector.py 中添加新的 API 端点

**Files:**
- Modify: `backend/src/api/vector.py`

**Step 1: 在文件末尾添加新的 API 端点**

在 `clear_all_vectors` 端点之后添加：

```python
@router.get("/indexed-files", response_model=List[Dict[str, Any]])
async def list_indexed_files():
    """获取所有已索引的文件列表"""
    try:
        files = lancedb_service.list_indexed_files()
        return files
    except Exception as e:
        logger.error(f"Failed to list indexed files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 2: 验证导入**

确保 `List` 和 `Dict` 已从 typing 导入。

---

## Task 3: 前端 - 在 vectorBackend.js 中添加 listIndexedFiles 方法

**Files:**
- Modify: `app/src/api/vectorBackend.js`

**Step 1: 查看现有文件结构**

先读取文件了解现有结构。

**Step 2: 添加 listIndexedFiles 静态方法**

在 VectorBackendApi 类中添加：

```javascript
static async listIndexedFiles() {
  try {
    const request = backend.client.get('/api/vector/indexed-files')
    return await request.json()
  } catch (error) {
    console.error('[VectorBackendApi] listIndexedFiles 失败:', error)
    throw new Error('获取已索引文件列表失败')
  }
}
```

---

## Task 4: 前端 - 在 vector.js store 中添加新状态和方法

**Files:**
- Modify: `app/src/stores/vector.js`

**Step 1: 添加新的响应式状态**

在现有 state 定义后添加：

```javascript
const indexedFiles = ref([])
const isLoadingIndexedFiles = ref(false)
```

**Step 2: 添加 loadIndexedFiles 方法**

在现有方法后添加：

```javascript
async function loadIndexedFiles() {
  isLoadingIndexedFiles.value = true
  error.value = null
  try {
    indexedFiles.value = await VectorBackendApi.listIndexedFiles()
    return indexedFiles.value
  } catch (err) {
    error.value = err.message
    throw err
  } finally {
    isLoadingIndexedFiles.value = false
  }
}
```

**Step 3: 在 return 语句中导出新状态和方法**

在 return 对象中添加：

```javascript
indexedFiles,
isLoadingIndexedFiles,
loadIndexedFiles,
```

---

## Task 5: 前端 - 修改 ParseDocumentsView.vue 添加标签页

**Files:**
- Modify: `app/src/components/parse/ParseDocumentsView.vue`

**Step 1: 添加 activeTab 状态**

在 script setup 中添加：

```javascript
const activeTab = ref('parse')
const selectedIndexedFile = ref(null)
```

**Step 2: 添加辅助方法**

在现有方法后添加：

```javascript
function formatDate(timestamp) {
  return new Date(timestamp * 1000).toLocaleString('zh-CN')
}

async function handleRefreshIndexedFiles() {
  try {
    await vectorStore.loadIndexedFiles()
    ElMessage.success('已刷新索引列表')
  } catch (err) {
    ElMessage.error(`刷新失败: ${err.message}`)
  }
}

function handleSelectIndexedFile(file) {
  selectedIndexedFile.value = file
  drawerVisible.value = true
}

async function handleDeleteIndexedFile(file) {
  try {
    await vectorStore.deleteDocumentChunks(file.file_path)
    ElMessage.success(`已删除 ${file.file_name} 的索引`)
    await handleRefreshIndexedFiles()
  } catch (err) {
    ElMessage.error(`删除失败: ${err.message}`)
  }
}
```

**Step 3: 更新 onMounted**

修改 onMounted，添加加载已索引文件：

```javascript
onMounted(async () => {
  try {
    await vectorStore.loadStats()
    await vectorStore.loadIndexedFiles()
  } catch (err) {
    console.error('加载失败:', err)
  }
})
```

**Step 4: 修改模板，添加 el-tabs**

将现有内容包裹在 `<el-tabs>` 中：

```vue
<template>
  <div class="parse-documents-view">
    <el-tabs v-model="activeTab" class="parse-tabs">
      <el-tab-pane label="解析任务" name="parse">
        <!-- 原有内容：view-header, document-grid 等 -->
        <div class="view-header">
          <h2>已解析文档</h2>
          <div class="header-tools">
            <el-button
              type="primary"
              size="small"
              :disabled="doneTasksWithoutIndex.length === 0 || vectorStore.isIndexing"
              :loading="vectorStore.isIndexing"
              @click="handleBatchIndex"
            >
              批量索引向量
            </el-button>
            <el-input
              v-model="searchText"
              placeholder="搜索文档..."
              prefix-icon="Search"
              style="width: 240px"
              clearable
            />
            <el-select v-model="statusFilter" placeholder="状态筛选" clearable style="width: 120px">
              <el-option label="全部" value="" />
              <el-option label="已完成" value="done" />
              <el-option label="解析中" value="running" />
              <el-option label="待解析" value="pending" />
              <el-option label="失败" value="failed" />
            </el-select>
          </div>
        </div>

        <div v-if="filteredTasks.length === 0" class="empty-state">
          <el-empty description="暂无解析文档" />
        </div>
        <div v-else class="document-grid">
          <div
            v-for="task in filteredTasks"
            :key="task.id"
            class="document-card"
            @click="handleSelectTask(task)"
          >
            <div class="card-header">
              <el-icon class="status-icon" :class="task.state">
                <CircleCheck v-if="task.state === 'done'" />
                <Loading v-else-if="task.state === 'running'" class="spinning" />
                <Clock v-else-if="task.state === 'pending'" />
                <CircleClose v-else />
              </el-icon>
              <div class="header-tags">
                <el-tag :type="parseStore.getStateType(task.state)" size="small">
                  {{ parseStore.getStateLabel(task.state) }}
                </el-tag>
                <el-tag
                  v-if="task.state === 'done'"
                  :type="vectorStore.isFileIndexed(task.file_path) ? 'success' : 'info'"
                  size="small"
                >
                  {{ vectorStore.isFileIndexed(task.file_path) ? '已索引' : '未索引' }}
                </el-tag>
              </div>
            </div>
            <div class="card-body">
              <div class="document-title">{{ task.file_name }}</div>
              <div class="document-path" :title="task.file_path">
                {{ task.file_path || '未知路径' }}
              </div>
            </div>
            <div class="card-footer">
              <span class="file-hash" v-if="task.file_hash"
                >{{ task.file_hash.substring(0, 16) }}...</span
              >
              <span class="parser-type">{{ task.parser_type || 'mineru' }}</span>
              <el-button
                v-if="task.state === 'done'"
                type="primary"
                size="small"
                link
                :loading="vectorStore.isIndexing && vectorStore.currentIndexingFile === task.file_name"
                @click.stop="handleIndexDocument(task)"
              >
                索引向量
              </el-button>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="向量索引" name="vector">
        <div class="view-header">
          <h2>向量索引管理</h2>
          <div class="header-tools">
            <el-button
              type="primary"
              size="small"
              :loading="vectorStore.isLoadingIndexedFiles"
              @click="handleRefreshIndexedFiles"
            >
              刷新
            </el-button>
          </div>
        </div>

        <div v-if="vectorStore.indexedFiles.length === 0" class="empty-state">
          <el-empty description="暂无索引文件" />
        </div>
        <div v-else class="document-grid">
          <div
            v-for="file in vectorStore.indexedFiles"
            :key="file.file_path"
            class="document-card"
            @click="handleSelectIndexedFile(file)"
          >
            <div class="card-header">
              <el-icon class="status-icon done">
                <CircleCheck />
              </el-icon>
              <div class="header-tags">
                <el-tag type="success" size="small">已索引</el-tag>
                <el-tag type="info" size="small">{{ file.chunk_count }} 分块</el-tag>
              </div>
            </div>
            <div class="card-body">
              <div class="document-title">{{ file.file_name }}</div>
              <div class="document-path" :title="file.file_path">
                {{ file.file_path || '未知路径' }}
              </div>
            </div>
            <div class="card-footer">
              <span class="file-hash">{{ formatDate(file.created_at) }}</span>
              <el-button
                type="danger"
                size="small"
                link
                @click.stop="handleDeleteIndexedFile(file)"
              >
                删除索引
              </el-button>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <ParseDetailsDrawer v-model:visible="drawerVisible" :task="selectedTask || selectedIndexedFile" />
  </div>
</template>
```

**Step 5: 添加标签页样式**

在 `<style scoped>` 末尾添加：

```css
.parse-tabs {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.parse-tabs :deep(.el-tabs__content) {
  flex: 1;
  overflow: hidden;
}

.parse-tabs :deep(.el-tab-pane) {
  height: 100%;
  display: flex;
  flex-direction: column;
}
```

---

## 验证清单

- [ ] 后端 API 端点 `/api/vector/indexed-files` 能正常返回数据
- [ ] 前端 vector store 的 `indexedFiles` 能正确加载数据
- [ ] 标签页切换功能正常
- [ ] 向量索引标签页能显示文件列表
- [ ] 删除索引功能正常
- [ ] 刷新功能正常
- [ ] Markdown 文件能在向量索引标签页中看到

---

Plan complete and saved to `docs/plans/2026-03-07-vector-index-management-tabs.md`. Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?
