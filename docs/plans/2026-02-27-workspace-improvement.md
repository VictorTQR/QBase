# 工作区管理功能完善 - 实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标**: 完善 QBase 工作区管理的基础功能，包括移除文件夹 UI、按需加载文件树、重复检测和状态管理优化。

**架构**: 
- 使用 Element Plus Tree 组件的 lazy 模式实现按需加载
- 通过右键菜单 + 确认弹窗实现文件夹移除
- 优化 workspace store，添加重复检测并完善现有方法

**技术栈**: Vue 3 + Pinia + Element Plus + Electron

---

## 前提条件

- 工作目录: `app/`
- 已运行 `npm install` 安装依赖

---

## Task 1: 优化 workspace store

**文件**:
- 修改: `app/src/stores/workspace.js`

### Step 1.1: 添加重复文件夹检测
在 `addFolder` 方法中添加路径重复检测，使用 `ElMessage` 提示用户。

### Step 1.2: 完善 refreshFileTree 方法
将其改为通知机制或直接标记需要刷新。

### Step 1.3: 清理未使用的 fileTree 状态
移除 `fileTree` 状态及其相关代码。

**最终代码参考**:
```javascript
import { ref } from 'vue'
import { defineStore } from 'pinia'
import { ElMessage } from 'element-plus'

export const useWorkspaceStore = defineStore(
  'workspace',
  () => {
    const folders = ref([])
    const activeFileId = ref(null)
    const needsRefresh = ref(false)

    function addFolder(folder) {
      const exists = folders.value.some(f => f.path === folder.path)
      if (exists) {
        ElMessage.warning('该文件夹已在工作区中')
        return
      }
      const newFolder = {
        id: Date.now().toString(),
        name: folder.name,
        path: folder.path,
        type: 'folder',
      }
      folders.value.push(newFolder)
      ElMessage.success('文件夹添加成功')
    }

    function removeFolder(folderId) {
      const index = folders.value.findIndex((f) => f.id === folderId)
      if (index !== -1) {
        folders.value.splice(index, 1)
        ElMessage.success('文件夹已移除')
      }
    }

    function refreshFileTree() {
      needsRefresh.value = !needsRefresh.value
    }

    function selectFile(fileId) {
      activeFileId.value = fileId
    }

    return {
      folders,
      activeFileId,
      needsRefresh,
      addFolder,
      removeFolder,
      refreshFileTree,
      selectFile,
    }
  },
  {
    persist: {
      key: 'qbase-workspace',
      paths: ['folders'],
    },
  },
)
```

### Step 1.4: 验证修改
检查代码语法正确，无 TypeScript 错误（如使用 JSDoc）。

---

## Task 2: 重构 Sidebar 组件 - 实现 lazy 加载

**文件**:
- 修改: `app/src/components/Layout/Sidebar.vue`

### Step 2.1: 重构 Tree 组件为 lazy 模式

修改模板部分，启用 lazy 加载：
```vue
<template>
  <div class="sidebar">
    <div class="workspace-header">
      <span class="workspace-title">工作区</span>
      <el-button :loading="isRefreshing" link type="primary" @click="handleRefresh">
        <el-icon><Refresh /></el-icon>
      </el-button>
    </div>
    <el-tree
      ref="treeRef"
      :data="treeData"
      :props="treeProps"
      lazy
      :load="loadNode"
      node-key="id"
      default-expand-all
      @node-click="handleNodeClick"
      @node-contextmenu="handleContextMenu"
      :highlight-current="true"
    />
    <teleport to="body">
      <div v-if="contextMenu.visible" class="context-menu" :style="contextMenu.style">
        <div class="context-menu-item" @click="handleRemoveFolder">移除文件夹</div>
      </div>
    </teleport>
  </div>
</template>
```

### Step 2.2: 实现 loadNode 方法
```javascript
async function loadNode(node, resolve) {
  if (node.level === 0) {
    const roots = workspaceStore.folders.map(f => ({
      ...f,
      leaf: false,
      loaded: false,
    }))
    return resolve(roots)
  }

  const nodeData = node.data
  if (nodeData.type === 'file') {
    return resolve([])
  }

  try {
    const result = await window.electronAPI.readDir(nodeData.path)
    if (result.success) {
      const children = [
        ...result.folders.map(f => ({ ...f, leaf: false, loaded: false })),
        ...result.files.map(f => ({ ...f, leaf: true })),
      ]
      return resolve(children)
    }
    return resolve([])
  } catch (error) {
    console.error('加载文件夹失败:', error)
    return resolve([])
  }
}
```

### Step 2.3: 实现右键菜单功能
```javascript
import { ref, onMounted, watch, onUnmounted } from 'vue'

const contextMenu = ref({
  visible: false,
  style: { left: '0px', top: '0px' },
  nodeData: null,
})

function handleContextMenu(event, data) {
  if (data.type === 'folder' && workspaceStore.folders.some(f => f.id === data.id)) {
    event.preventDefault()
    contextMenu.value = {
      visible: true,
      style: { left: `${event.clientX}px`, top: `${event.clientY}px` },
      nodeData: data,
    }
  }
}

function handleClickOutside() {
  contextMenu.value.visible = false
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
```

### Step 2.4: 实现移除文件夹确认
```javascript
import { ElMessageBox, ElMessage } from 'element-plus'

async function handleRemoveFolder() {
  contextMenu.value.visible = false
  try {
    await ElMessageBox.confirm(
      `确定要移除文件夹「${contextMenu.value.nodeData.name}」吗？`,
      '移除文件夹',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    workspaceStore.removeFolder(contextMenu.value.nodeData.id)
  } catch {
  }
}
```

### Step 2.5: 更新 refreshTree 和其他辅助方法
简化 `refreshTree`，使用 `treeRef` 来刷新：
```javascript
const treeRef = ref(null)

async function handleRefresh() {
  isRefreshing.value = true
  try {
    if (treeRef.value) {
      treeRef.value.updateKeyChildren()
    }
  } finally {
    isRefreshing.value = false
  }
}

watch(
  () => workspaceStore.folders,
  () => {
    if (treeRef.value) {
      treeRef.value.updateKeyChildren()
    }
  },
  { deep: true },
)

onMounted(() => {
})
```

### Step 2.6: 添加右键菜单样式
```css
.context-menu {
  position: fixed;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  z-index: 3000;
  min-width: 120px;
}

.context-menu-item {
  padding: 8px 16px;
  cursor: pointer;
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.context-menu-item:hover {
  background: var(--el-fill-color-light);
}
```

---

## Task 3: 更新 MainLayout 组件（可选优化）

**文件**:
- 修改: `app/src/components/Layout/MainLayout.vue`

### Step 3.1: 利用 store 中的成功提示
保持现有代码不变，store 已添加 `ElMessage` 提示。

---

## Task 4: 测试验证

### Step 4.1: 手动测试清单

| 测试项 | 预期结果 |
|--------|----------|
| 添加已存在的文件夹 | 显示「该文件夹已在工作区中」提示 |
| 右键点击根文件夹 | 显示「移除文件夹」菜单 |
| 点击「移除文件夹」 | 弹出确认对话框 |
| 确认移除 | 文件夹从列表中移除，显示成功提示 |
| 展开深层文件夹 | 子文件/文件夹动态加载 |
| 点击刷新按钮 | 文件树刷新 |
| 点击文件 | 文件正常预览（现有功能） |

### Step 4.2: 运行现有测试
```bash
cd app
npm run test:unit
```
确保现有测试通过（虽然测试内容可能过时）。

### Step 4.3: 运行代码检查
```bash
npm run lint
npm run format
```

---

## Task 5: 更新文档（可选）

**文件**:
- 更新: `docs/features/workspace.md` - 标记相关功能为已完成

---

## 验收清单

- [ ] Task 1 完成: workspace store 优化完成
- [ ] Task 2 完成: Sidebar 组件重构完成
- [ ] Task 3 完成: MainLayout 验证完成
- [ ] Task 4 完成: 所有测试项验证通过
- [ ] Task 5 完成: 文档更新（如需要）
- [ ] `npm run lint` 通过
- [ ] `npm run format` 通过
- [ ] 应用能正常启动，功能正常

---

## 执行方式选择

计划已保存至 `docs/plans/2026-02-27-workspace-improvement.md`。

**两种执行方式:**

1. **Subagent-Driven (本次会话)** - 每个任务派遣独立子代理，逐个执行并review
2. **手动执行** - 按照上述步骤手动修改代码

请选择执行方式？
