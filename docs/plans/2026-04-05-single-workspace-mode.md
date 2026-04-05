# 单工作区模式改造实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 QBase 改造为 Obsidian 风格的单工作区模式，支持工作区选择/打开、记住上次工作区、工作区切换等功能。

**Architecture:** 采用全局工作区配置 (~/.qbase/workspaces.json) + 每个工作区本地配置 (.qbase/config.json)，启动时自动打开上次工作区，支持工作区切换。

**Tech Stack:** Vue 3, Pinia, Electron, LocalStorage, File System

---

## 任务 1: 全局工作区配置管理

**Files:**
- Create: `app/src/utils/workspaceManager.js`

**Step 1: 创建工作区管理器**

创建 `app/src/utils/workspaceManager.js`：

```javascript
import { app } from '@electron/remote'
import path from 'path'
import fs from 'fs'

class WorkspaceManager {
  constructor() {
    this.globalConfigDir = this.getGlobalConfigDir()
    this.workspacesFilePath = path.join(this.globalConfigDir, 'workspaces.json')
    this.ensureGlobalConfigDir()
  }

  getGlobalConfigDir() {
    // 获取用户目录下的 .qbase 配置目录
    const homeDir = app.getPath('home')
    return path.join(homeDir, '.qbase')
  }

  ensureGlobalConfigDir() {
    if (!fs.existsSync(this.globalConfigDir)) {
      fs.mkdirSync(this.globalConfigDir, { recursive: true })
    }
  }

  loadWorkspaces() {
    if (!fs.existsSync(this.workspacesFilePath)) {
      return { workspaces: [], lastWorkspace: null }
    }
    try {
      const content = fs.readFileSync(this.workspacesFilePath, 'utf-8')
      return JSON.parse(content)
    } catch (error) {
      console.error('加载工作区配置失败:', error)
      return { workspaces: [], lastWorkspace: null }
    }
  }

  saveWorkspaces(config) {
    try {
      fs.writeFileSync(
        this.workspacesFilePath,
        JSON.stringify(config, null, 2),
        'utf-8'
      )
    } catch (error) {
      console.error('保存工作区配置失败:', error)
    }
  }

  addWorkspace(workspacePath) {
    const config = this.loadWorkspaces()
    const normalizedPath = path.normalize(workspacePath)
    
    // 检查是否已存在
    const exists = config.workspaces.some(w => path.normalize(w.path) === normalizedPath)
    if (!exists) {
      config.workspaces.push({
        path: normalizedPath,
        name: path.basename(normalizedPath),
        addedAt: Date.now(),
      })
    }
    
    // 设置为上次打开的工作区
    config.lastWorkspace = normalizedPath
    this.saveWorkspaces(config)
    
    return config
  }

  setLastWorkspace(workspacePath) {
    const config = this.loadWorkspaces()
    config.lastWorkspace = path.normalize(workspacePath)
    this.saveWorkspaces(config)
  }

  getLastWorkspace() {
    const config = this.loadWorkspaces()
    return config.lastWorkspace
  }

  removeWorkspace(workspacePath) {
    const config = this.loadWorkspaces()
    const normalizedPath = path.normalize(workspacePath)
    config.workspaces = config.workspaces.filter(w => path.normalize(w.path) !== normalizedPath)
    
    // 如果删除的是上次打开的工作区，清空
    if (config.lastWorkspace === normalizedPath) {
      config.lastWorkspace = config.workspaces.length > 0 ? config.workspaces[0].path : null
    }
    
    this.saveWorkspaces(config)
    return config
  }

  getAllWorkspaces() {
    const config = this.loadWorkspaces()
    return config.workspaces
  }
}

export const workspaceManager = new WorkspaceManager()
```

**Step 2: 提交更改**

```bash
git add app/src/utils/workspaceManager.js
git commit -m "feat: 创建全局工作区配置管理器"
```

---

## 任务 2: 工作区选择/打开界面

**Files:**
- Create: `app/src/views/WorkspaceSelector.vue`
- Create: `app/src/components/WorkspaceCard.vue`

**Step 1: 创建工作区卡片组件**

创建 `app/src/components/WorkspaceCard.vue`：

```vue
<template>
  <div class="workspace-card" @click="handleClick">
    <div class="card-icon">📁</div>
    <div class="card-content">
      <div class="card-name">{{ workspace.name }}</div>
      <div class="card-path">{{ workspace.path }}</div>
    </div>
    <div class="card-actions" @click.stop>
      <el-button link type="danger" size="small" @click="handleRemove">
        <el-icon><Delete /></el-icon>
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { Delete } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'

const props = defineProps({
  workspace: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['select', 'remove'])

function handleClick() {
  emit('select', props.workspace)
}

async function handleRemove() {
  try {
    await ElMessageBox.confirm(
      `确定要移除工作区「${props.workspace.name}」吗？`,
      '移除工作区',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    emit('remove', props.workspace)
  } catch {
    // 用户取消
  }
}
</script>

<style scoped>
.workspace-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.workspace-card:hover {
  border-color: var(--el-color-primary);
  background-color: var(--el-fill-color-lighter);
}

.card-icon {
  font-size: 32px;
  flex-shrink: 0;
}

.card-content {
  flex: 1;
  min-width: 0;
}

.card-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
}

.card-path {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-actions {
  flex-shrink: 0;
}
</style>
```

**Step 2: 创建工作区选择视图**

创建 `app/src/views/WorkspaceSelector.vue`：

```vue
<template>
  <div class="workspace-selector">
    <div class="selector-header">
      <h1>QBase</h1>
      <p class="subtitle">选择或创建工作区</p>
    </div>

    <div class="selector-content">
      <!-- 现有工作区列表 -->
      <div v-if="workspaces.length > 0" class="workspace-list">
        <div class="section-title">
          <span>最近打开</span>
        </div>
        <div class="workspace-grid">
          <WorkspaceCard
            v-for="workspace in workspaces"
            :key="workspace.path"
            :workspace="workspace"
            @select="handleSelectWorkspace"
            @remove="handleRemoveWorkspace"
          />
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="actions">
        <el-button type="primary" size="large" @click="handleOpenWorkspace">
          <el-icon><FolderOpened /></el-icon>
          打开文件夹作为工作区
        </el-button>
        <el-button size="large" @click="handleCreateWorkspace">
          <el-icon><FolderAdd /></el-icon>
          创建新工作区
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { FolderOpened, FolderAdd } from '@element-plus/icons-vue'
import { workspaceManager } from '@/utils/workspaceManager'
import WorkspaceCard from '@/components/WorkspaceCard.vue'

const router = useRouter()
const workspaces = ref([])

function loadWorkspaces() {
  workspaces.value = workspaceManager.getAllWorkspaces()
}

async function handleOpenWorkspace() {
  try {
    const result = await window.electronAPI.selectFolder()
    if (result) {
      openWorkspace(result.path)
    }
  } catch (error) {
    console.error('打开工作区失败:', error)
  }
}

async function handleCreateWorkspace() {
  try {
    const result = await window.electronAPI.selectFolder()
    if (result) {
      openWorkspace(result.path)
    }
  } catch (error) {
    console.error('创建工作区失败:', error)
  }
}

function handleSelectWorkspace(workspace) {
  openWorkspace(workspace.path)
}

function handleRemoveWorkspace(workspace) {
  workspaceManager.removeWorkspace(workspace.path)
  loadWorkspaces()
  ElMessage.success('工作区已移除')
}

function openWorkspace(workspacePath) {
  // 保存到全局配置
  workspaceManager.addWorkspace(workspacePath)
  
  // 保存到 Pinia store（后续创建）
  // workspaceStore.setCurrentWorkspace(workspacePath)
  
  // 跳转到主页
  ElMessage.success('工作区已打开')
  router.push('/')
}

onMounted(() => {
  loadWorkspaces()
  
  // 检查是否有上次打开的工作区，有则自动打开
  const lastWorkspace = workspaceManager.getLastWorkspace()
  if (lastWorkspace) {
    openWorkspace(lastWorkspace)
  }
})
</script>

<style scoped>
.workspace-selector {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.selector-header {
  text-align: center;
  margin-bottom: 48px;
  color: white;
}

.selector-header h1 {
  font-size: 48px;
  font-weight: 700;
  margin-bottom: 8px;
}

.subtitle {
  font-size: 18px;
  opacity: 0.9;
}

.selector-content {
  width: 100%;
  max-width: 800px;
  background: white;
  border-radius: 16px;
  padding: 32px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 16px;
}

.workspace-list {
  margin-bottom: 32px;
}

.workspace-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.actions {
  display: flex;
  gap: 16px;
  justify-content: center;
}
</style>
```

**Step 3: 提交更改**

```bash
git add app/src/components/WorkspaceCard.vue
git add app/src/views/WorkspaceSelector.vue
git commit -m "feat: 创建工作区选择界面组件"
```

---

## 任务 3: 重构 Workspace Store

**Files:**
- Modify: `app/src/stores/workspace.js`

**Step 1: 重构为单工作区模式**

编辑 `app/src/stores/workspace.js`，替换为：

```javascript
import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { workspaceManager } from '@/utils/workspaceManager'

export const useWorkspaceStore = defineStore(
  'workspace',
  () => {
    const currentWorkspace = ref(null)
    const activeFileId = ref(null)
    const needsRefresh = ref(false)

    const isWorkspaceSelected = computed(() => currentWorkspace.value !== null)
    const workspaceName = computed(() => {
      if (!currentWorkspace.value) return ''
      return currentWorkspace.value.split(/[/\\]/).pop()
    })

    function setCurrentWorkspace(workspacePath) {
      currentWorkspace.value = workspacePath
      // 保存到全局配置
      workspaceManager.setLastWorkspace(workspacePath)
    }

    function clearCurrentWorkspace() {
      currentWorkspace.value = null
    }

    function refreshFileTree() {
      needsRefresh.value = !needsRefresh.value
    }

    function selectFile(fileId) {
      activeFileId.value = fileId
    }

    // 初始化时加载上次工作区
    function initializeFromLastWorkspace() {
      const lastWorkspace = workspaceManager.getLastWorkspace()
      if (lastWorkspace) {
        currentWorkspace.value = lastWorkspace
      }
    }

    return {
      currentWorkspace,
      activeFileId,
      needsRefresh,
      isWorkspaceSelected,
      workspaceName,
      setCurrentWorkspace,
      clearCurrentWorkspace,
      refreshFileTree,
      selectFile,
      initializeFromLastWorkspace,
    }
  },
  {
    persist: {
      key: 'qbase-workspace',
      paths: ['currentWorkspace'],
    },
  },
)
```

**Step 2: 提交更改**

```bash
git add app/src/stores/workspace.js
git commit -m "feat: 重构 Workspace Store 为单工作区模式"
```

---

## 任务 4: 更新路由配置

**Files:**
- Modify: `app/src/router/index.js`

**Step 1: 添加工作区选择路由**

编辑 `app/src/router/index.js`，更新为：

```javascript
import { createRouter, createWebHistory } from 'vue-router'
import { useWorkspaceStore } from '@/stores/workspace'

const routes = [
  {
    path: '/workspace-selector',
    name: 'workspace-selector',
    component: () => import('@/views/WorkspaceSelector.vue'),
  },
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/Home.vue'),
    meta: { requiresWorkspace: true },
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('@/views/Settings.vue'),
    meta: { requiresWorkspace: true },
  },
  {
    path: '/parse-management',
    name: 'parse-management',
    component: () => import('@/views/ParseManagement.vue'),
    meta: { requiresWorkspace: true },
  },
  {
    path: '/papers',
    name: 'Papers',
    component: () => import('@/views/PapersView.vue'),
    meta: { title: '论文管理', requiresWorkspace: true },
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

// 路由守卫：检查是否选择了工作区
router.beforeEach((to, from, next) => {
  const workspaceStore = useWorkspaceStore()
  
  if (to.meta.requiresWorkspace && !workspaceStore.isWorkspaceSelected) {
    // 需要工作区但未选择，跳转到选择界面
    next('/workspace-selector')
  } else if (to.path === '/workspace-selector' && workspaceStore.isWorkspaceSelected) {
    // 已选择工作区但访问选择界面，跳转到主页
    next('/')
  } else {
    next()
  }
})

export default router
```

**Step 2: 提交更改**

```bash
git add app/src/router/index.js
git commit -m "feat: 更新路由配置，添加工作区选择路由和守卫"
```

---

## 任务 5: 简化侧边栏组件

**Files:**
- Modify: `app/src/components/Layout/Sidebar.vue`

**Step 1: 移除旧架构代码，优化新架构 UI**

编辑 `app/src/components/Layout/Sidebar.vue`，简化为：

```vue
<template>
  <div class="sidebar">
    <div class="sidebar-header">
      <div class="workspace-info">
        <span class="workspace-icon">📁</span>
        <span class="workspace-name">{{ workspaceStore.workspaceName }}</span>
      </div>
      <div class="header-actions">
        <el-button :loading="fileManagementStore.isScanning" link type="primary" @click="handleScan">
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- 扫描统计 -->
    <div v-if="fileManagementStore.scanStats" class="scan-stats">
      <span class="stat-item">新增: {{ fileManagementStore.scanStats.new_files }}</span>
      <span class="stat-item">修改: {{ fileManagementStore.scanStats.modified_files }}</span>
    </div>

    <div class="file-tree-container">
      <!-- 新架构：基于 files 表的文件列表 -->
      <div v-if="fileManagementStore.files.length > 0" class="file-list">
        <div
          v-for="file in fileManagementStore.files"
          :key="file.hash"
          class="file-item"
          :class="{ active: fileManagementStore.selectedFile?.hash === file.hash }"
          @click="handleFileClick(file)"
        >
          <span class="file-icon">{{ getFileIcon(file.file_type) }}</span>
          <span class="file-name">{{ file.rel_path.split('/').pop() }}</span>
          <span class="file-status" :class="file.status">{{ getStatusText(file.status) }}</span>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else class="empty-state">
        <el-empty description="暂无文件，点击刷新按钮扫描" />
      </div>
    </div>

    <div class="sidebar-footer">
      <el-button type="primary" class="parse-management-btn" @click="goToParseManagement">
        <el-icon><Document /></el-icon>
        <span>解析管理</span>
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Refresh, Document } from '@element-plus/icons-vue'
import { useWorkspaceStore } from '@/stores/workspace'
import { useDocumentStore } from '@/stores/document'
import { useFileManagementStore } from '@/stores/fileManagement'

const router = useRouter()
const workspaceStore = useWorkspaceStore()
const documentStore = useDocumentStore()
const fileManagementStore = useFileManagementStore()

function getFileIcon(fileType) {
  const icons = {
    'markdown': '📝',
    'pdf': '📄',
    'audio': '🎵',
    'video': '🎬',
  }
  return icons[fileType] || '📄'
}

function getStatusText(status) {
  const texts = {
    'pending': '待处理',
    'processing': '处理中',
    'ready': '就绪',
    'error': '错误',
    'missing': '缺失',
    'orphan': '孤立',
  }
  return texts[status] || status
}

async function handleFileClick(file) {
  fileManagementStore.selectFile(file)
  
  // 转换为旧格式兼容
  const workspacePath = workspaceStore.currentWorkspace
  if (workspacePath) {
    const fullPath = `${workspacePath}/${file.rel_path}`
    const fileData = {
      id: file.hash,
      name: file.rel_path.split('/').pop(),
      path: fullPath,
      type: 'file',
      fileType: file.file_type,
    }
    documentStore.loadFile(fileData)
  }
}

async function handleScan() {
  const workspacePath = workspaceStore.currentWorkspace
  if (workspacePath) {
    await fileManagementStore.initializeAndScanWorkspace(workspacePath)
  }
}

function goToParseManagement() {
  router.push('/parse-management')
}

onMounted(() => {
  // 自动扫描工作区
  const workspacePath = workspaceStore.currentWorkspace
  if (workspacePath) {
    fileManagementStore.initializeAndScanWorkspace(workspacePath)
  }
})
</script>

<style scoped>
.sidebar {
  width: 25%;
  min-width: 200px;
  border-right: 1px solid var(--el-border-color);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}

.workspace-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.workspace-icon {
  font-size: 18px;
  flex-shrink: 0;
}

.workspace-name {
  font-weight: 600;
  font-size: 14px;
  color: var(--el-text-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.header-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.scan-stats {
  padding: 8px 16px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  border-bottom: 1px solid var(--el-border-color-lighter);
  display: flex;
  gap: 16px;
}

.stat-item {
  display: inline-flex;
  align-items: center;
}

.file-tree-container {
  flex: 1;
  overflow-y: auto;
  padding: 4px 0;
}

.file-list {
  display: flex;
  flex-direction: column;
}

.file-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
  gap: 8px;
  transition: background-color 0.2s;
}

.file-item:hover {
  background-color: var(--el-fill-color-light);
}

.file-item.active {
  background-color: var(--el-fill-color);
}

.file-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.file-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
}

.file-status {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  flex-shrink: 0;
}

.file-status.pending {
  background-color: var(--el-color-warning-light-9);
  color: var(--el-color-warning);
}

.file-status.processing {
  background-color: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}

.file-status.ready {
  background-color: var(--el-color-success-light-9);
  color: var(--el-color-success);
}

.file-status.error {
  background-color: var(--el-color-danger-light-9);
  color: var(--el-color-danger);
}

.file-status.missing {
  background-color: var(--el-color-info-light-9);
  color: var(--el-color-info);
}

.empty-state {
  padding: 32px 16px;
}

.sidebar-footer {
  padding: 12px 16px;
  border-top: 1px solid var(--el-border-color-lighter);
  flex-shrink: 0;
}

.parse-management-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
</style>
```

**Step 2: 提交更改**

```bash
git add app/src/components/Layout/Sidebar.vue
git commit -m "feat: 简化侧边栏组件，移除旧架构代码"
```

---

## 任务 6: 主布局改造

**Files:**
- Modify: `app/src/components/Layout/MainLayout.vue`

**Step 1: 改造主布局，添加工作区切换**

编辑 `app/src/components/Layout/MainLayout.vue`，替换为：

```vue
<template>
  <div class="main-layout">
    <header class="header">
      <div class="logo">QBase</div>
      <div class="workspace-display" @click="handleOpenWorkspaceSelector">
        <el-icon><Folder /></el-icon>
        <span class="workspace-name">{{ workspaceStore.workspaceName }}</span>
        <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
      </div>
      <div class="actions">
        <el-button @click="handleOpenSearch" link>
          <el-icon><Search /></el-icon>
          <span class="search-hint">搜索 (Ctrl+K)</span>
        </el-button>
        <el-button @click="handleOpenSettings" link>
          <el-icon><Setting /></el-icon>
        </el-button>
      </div>
    </header>
    <div class="content">
      <slot />
    </div>
    <SearchPanel />
  </div>
</template>

<script setup>
import { Folder, Search, Setting, ArrowDown } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { useWorkspaceStore } from '@/stores/workspace'
import { useSearchStore } from '@/stores/search'
import { workspaceManager } from '@/utils/workspaceManager'
import SearchPanel from '@/components/SearchPanel.vue'

const router = useRouter()
const workspaceStore = useWorkspaceStore()
const searchStore = useSearchStore()

function handleOpenWorkspaceSelector() {
  router.push('/workspace-selector')
}

function handleOpenSearch() {
  searchStore.openPanel()
}

function handleOpenSettings() {
  router.push('/settings')
}
</script>

<style scoped>
.main-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--el-bg-color);
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  height: 48px;
  border-bottom: 1px solid var(--el-border-color);
}

.logo {
  font-size: 18px;
  font-weight: bold;
  color: var(--el-text-color-primary);
}

.workspace-display {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.workspace-display:hover {
  background-color: var(--el-fill-color-light);
}

.workspace-name {
  font-size: 14px;
  color: var(--el-text-color-primary);
}

.dropdown-icon {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.search-hint {
  font-size: 14px;
}

@media (max-width: 768px) {
  .search-hint {
    display: none;
  }
}

.content {
  flex: 1;
  display: flex;
  overflow: hidden;
}
</style>
```

**Step 2: 提交更改**

```bash
git add app/src/components/Layout/MainLayout.vue
git commit -m "feat: 主布局改造 - 工作区显示和切换"
```

---

## 任务 7: 更新主入口和 App.vue

**Files:**
- Modify: `app/src/App.vue`

**Step 1: 更新 App.vue，初始化工作区**

编辑 `app/src/App.vue`，添加工作区初始化：

```vue
<template>
  <router-view />
</template>

<script setup>
import { onMounted } from 'vue'
import { useWorkspaceStore } from '@/stores/workspace'

const workspaceStore = useWorkspaceStore()

onMounted(() => {
  // 从持久化存储或上次工作区初始化
  workspaceStore.initializeFromLastWorkspace()
})
</script>
```

**Step 2: 提交更改**

```bash
git add app/src/App.vue
git commit -m "feat: 更新 App.vue，初始化工作区"
```

---

## 验证与测试

**运行前端：**

```bash
cd app
npm run dev
```

**测试步骤：**

1. 首次启动应该显示工作区选择界面
2. 点击"打开文件夹作为工作区"
3. 选择一个文件夹，应该自动跳转到主页
4. 侧边栏显示工作区名称和文件列表
5. 顶部显示当前工作区，点击可以切换
6. 重新启动应用，应该自动打开上次工作区

---

## 总结

本计划完成了单工作区模式的所有改造：

✅ **全局配置管理** - ~/.qbase/workspaces.json  
✅ **工作区选择界面** - WorkspaceSelector + WorkspaceCard  
✅ **Store 重构** - 单工作区模式，记住上次工作区  
✅ **路由更新** - 工作区选择路由 + 路由守卫  
✅ **侧边栏简化** - 移除旧架构，优化新架构 UI  
✅ **主布局改造** - 工作区显示和切换按钮  
✅ **应用初始化** - 自动加载上次工作区  

至此，QBase 已改造为 Obsidian 风格的单工作区模式！
