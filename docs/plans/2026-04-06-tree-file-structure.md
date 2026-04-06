# 左侧边栏树形文件结构实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标：** 将左侧工作区从平铺列表改为使用 Element Plus el-tree 的完整树形结构

**架构：** 创建树形数据转换工具函数，修改 Sidebar.vue 使用 el-tree 组件，自定义节点内容渲染

**技术栈：** Vue 3, Pinia, Element Plus (el-tree)

---

### 任务 1: 创建树形数据转换工具函数

**文件：**
- 创建: `app/src/utils/treeUtils.js`

**Step 1: 创建 treeUtils.js 文件**

写入以下内容：

```javascript
export function buildFileTree(files) {
  const tree = []
  const pathMap = {}

  files.forEach((file) => {
    const parts = file.rel_path.split('/')
    let currentLevel = tree

    parts.forEach((part, index) => {
      const fullPath = parts.slice(0, index + 1).join('/')
      const isFile = index === parts.length - 1

      if (!pathMap[fullPath]) {
        const node = {
          label: part,
          children: [],
          isFile,
          file: isFile ? file : null,
        }
        pathMap[fullPath] = node
        currentLevel.push(node)
      }

      currentLevel = pathMap[fullPath].children
    })
  })

  return tree
}

export function flattenTree(nodes, result = []) {
  nodes.forEach((node) => {
    if (node.isFile) {
      result.push(node.file)
    }
    if (node.children && node.children.length > 0) {
      flattenTree(node.children, result)
    }
  })
  return result
}
```

**Step 2: 验证**
- 文件路径正确
- 函数语法正确
- 包含两个函数：`buildFileTree` 和 `flattenTree`

**Step 3: 提交**
```bash
git add app/src/utils/treeUtils.js
git commit -m "feat: 添加树形数据转换工具函数"
```

---

### 任务 2: 修改 Sidebar.vue 使用 el-tree

**文件：**
- 修改: `app/src/components/Layout/Sidebar.vue`

**Step 1: 导入 treeUtils**
在 script setup 顶部导入区域添加：
```javascript
import { buildFileTree } from '@/utils/treeUtils'
```

**Step 2: 添加 treeData 计算属性**
在 script setup 中添加：
```javascript
const treeData = computed(() => {
  return buildFileTree(fileManagementStore.files)
})
```

**Step 3: 添加 el-tree 节点内容渲染函数**
在 script setup 中添加：
```javascript
function renderTreeNodeContent({ node, data }) {
  if (data.isFile && data.file) {
    return h('div', { class: 'tree-node-content' }, [
      h('span', { class: 'file-icon' }, getFileIcon(data.file.file_type)),
      h('span', { class: 'file-name' }, data.label),
      h('span', { class: ['file-status', data.file.status] }, getStatusText(data.file.status)),
    ])
  }
  return h('div', { class: 'tree-node-content' }, [
    h('span', { class: 'folder-icon' }, '📁'),
    h('span', { class: 'folder-name' }, data.label),
  ])
}
```

**Step 4: 导入 h 函数**
在 import 语句中添加 `h`：
```javascript
import { ref, onMounted, computed, h } from 'vue'
```

**Step 5: 替换模板中的文件列表为 el-tree**
将原有的 file-list div（第20-38行）替换为：
```vue
<div class="file-tree-container">
  <el-tree
    v-if="treeData.length > 0"
    :data="treeData"
    :props="{ children: 'children', label: 'label' }"
    node-key="label"
    default-expand-all
    :expand-on-click-node="false"
    @node-click="handleNodeClick"
  >
    <template #default="{ node, data }">
      <div
        class="custom-tree-node"
        :class="{ active: data.isFile && fileManagementStore.selectedFile?.hash === data.file?.hash }"
      >
        <span v-if="data.isFile" class="file-icon">{{ getFileIcon(data.file.file_type) }}</span>
        <span v-else class="folder-icon">📁</span>
        <span class="node-label">{{ data.label }}</span>
        <span v-if="data.isFile" class="file-status" :class="data.file.status">
          {{ getStatusText(data.file.status) }}
        </span>
      </div>
    </template>
  </el-tree>

  <div v-else class="empty-state">
    <el-empty description="暂无文件，点击刷新按钮扫描" />
  </div>
</div>
```

**Step 6: 添加 handleNodeClick 函数**
在 script setup 中添加：
```javascript
function handleNodeClick(data) {
  if (data.isFile && data.file) {
    handleFileClick(data.file)
  }
}
```

**Step 7: 添加样式**
在 `<style scoped>` 中添加：
```css
.custom-tree-node {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
  gap: 8px;
  transition: background-color 0.2s;
  flex: 1;
  min-width: 0;
}

.custom-tree-node:hover {
  background-color: var(--el-fill-color-light);
}

.custom-tree-node.active {
  background-color: var(--el-fill-color);
}

.node-label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
}

.folder-icon,
.file-icon {
  font-size: 16px;
  flex-shrink: 0;
}

:deep(.el-tree-node__content) {
  padding: 0 !important;
  height: auto !important;
}

:deep(.el-tree) {
  --el-tree-node-padding: 4px 0;
}
```

**Step 8: 验证**
- 所有导入正确
- 计算属性正确
- 模板正确替换
- 样式正确添加

**Step 9: 提交**
```bash
git add app/src/components/Layout/Sidebar.vue
git commit -m "feat: 使用 el-tree 重构侧边栏文件树"
```

---

### 任务 3: 运行 lint 和 format

**文件：**
- 检查: `app/src/utils/treeUtils.js`
- 检查: `app/src/components/Layout/Sidebar.vue`

**Step 1: 运行 lint**
```bash
cd app
npm run lint
```

**Step 2: 运行 format**
```bash
npm run format
```

**Step 3: 提交格式化更改（如果有）**
```bash
git add app/src/utils/treeUtils.js app/src/components/Layout/Sidebar.vue
git commit -m "style: 应用 lint 和 format 规则"
```

---

### 任务 4: 验证功能

**Step 1: 启动应用**
```bash
cd app
npm run dev
```

**Step 2: 测试树形显示**
- 验证文件以树形结构显示
- 文件夹可展开/折叠
- 文件显示正确的图标和状态

**Step 3: 测试文件选择**
- 点击文件时高亮正确
- 点击文件夹时不触发文件加载

---

## 执行交接

计划已保存至 `docs/plans/2026-04-06-tree-file-structure.md`。两个执行选项：

**1. Subagent-Driven (本会话)** - 我为每个任务分派新的子代理，任务间进行代码审查，快速迭代

**2. Parallel Session (独立会话)** - 使用 executing-plans 开启新会话，带检查点的批量执行

选择哪种方式？
