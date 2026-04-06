# 修复左侧工作区文件树显示问题实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标：** 修复 QBase 项目左侧工作区文件树不显示的问题

**架构：** 问题根源在于 `fileManagement.js` 访问了不存在的 `workspaceStore.folders` 属性，需要修改为使用正确的 `workspaceStore.currentWorkspace`。同时需要修复 `WorkspaceSelector.vue` 中缺少的工作区状态更新。

**技术栈：** Vue 3, Pinia, Element Plus

---

### 任务 1: 修复 fileManagement.js 中的 currentWorkspacePath

**文件：**
- 修改: `app/src/stores/fileManagement.js:19-24`

**步骤 1: 理解当前问题**
当前代码访问 `workspaceStore.folders`，但该属性不存在。

**步骤 2: 修改 currentWorkspacePath computed 属性**
将以下代码：
```javascript
const currentWorkspacePath = computed(() => {
  if (workspaceStore.folders.length > 0) {
    return workspaceStore.folders[0].path
  }
  return null
})
```

替换为：
```javascript
const currentWorkspacePath = computed(() => {
  return workspaceStore.currentWorkspace
})
```

**步骤 3: 验证修改**
确保代码语法正确，没有引用错误。

**步骤 4: 提交**
```bash
git add app/src/stores/fileManagement.js
git commit -m "fix: 修复 fileManagement 中 currentWorkspacePath 访问错误"
```

---

### 任务 2: 修复 WorkspaceSelector.vue 中的工作区更新

**文件：**
- 修改: `app/src/views/WorkspaceSelector.vue:86-91`

**步骤 1: 添加 workspaceStore 导入**
在 script setup 顶部添加：
```javascript
import { useWorkspaceStore } from '@/stores/workspace'
```

**步骤 2: 初始化 workspaceStore**
在 `const router = useRouter()` 后添加：
```javascript
const workspaceStore = useWorkspaceStore()
```

**步骤 3: 修改 openWorkspace 函数**
将：
```javascript
function openWorkspace(workspacePath) {
  workspaceManager.addWorkspace(workspacePath)

  ElMessage.success('工作区已打开')
  router.push('/')
}
```

修改为：
```javascript
async function openWorkspace(workspacePath) {
  workspaceManager.addWorkspace(workspacePath)
  await workspaceStore.setCurrentWorkspace(workspacePath)

  ElMessage.success('工作区已打开')
  router.push('/')
}
```

**步骤 4: 验证修改**
确保函数签名正确（async），调用了 `setCurrentWorkspace`。

**步骤 5: 提交**
```bash
git add app/src/views/WorkspaceSelector.vue
git commit -m "fix: 修复工作区选择器中 workspaceStore 状态更新"
```

---

### 任务 3: 运行 lint 和 format 检查

**文件：**
- 检查: `app/src/stores/fileManagement.js`
- 检查: `app/src/views/WorkspaceSelector.vue`

**步骤 1: 运行 lint**
```bash
cd app
npm run lint
```

**步骤 2: 运行 format**
```bash
npm run format
```

**步骤 3: 提交格式化更改（如果有）**
```bash
git add app/src/stores/fileManagement.js app/src/views/WorkspaceSelector.vue
git commit -m "style: 应用 lint 和 format 规则"
```

---

### 任务 4: 验证修复

**步骤 1: 检查控制台是否有错误**
运行应用并检查浏览器控制台是否还有关于 `folders` 未定义的错误。

**步骤 2: 测试工作区选择**
- 打开应用
- 选择或创建工作区
- 验证左侧文件树是否正常显示

**步骤 3: 测试文件扫描**
- 点击刷新按钮
- 验证文件扫描和列表加载是否正常

---

## 执行交接

计划已保存至 `docs/plans/2026-04-06-fix-file-tree-display.md`。两个执行选项：

**1. Subagent-Driven (本会话)** - 我为每个任务分派新的子代理，任务间进行代码审查，快速迭代

**2. Parallel Session (独立会话)** - 使用 executing-plans 开启新会话，带检查点的批量执行

选择哪种方式？
