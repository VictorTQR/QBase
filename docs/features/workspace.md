# 工作区管理

**状态**: ✅ 已完成
**版本**: v0.1
**更新日期**: 2026-02-25

## 功能概述

工作区管理功能允许用户添加和管理本地文件夹，构建个人知识库的文件索引。

## 核心功能

### 添加文件夹

- 通过 Electron API 打开系统文件夹选择对话框
- 递归扫描文件夹内容
- 构建文件树结构

### 移除文件夹

- 从工作区列表中移除
- 清除相关缓存

### 文件树导航

- 树形展示文件夹结构
- 支持展开/折叠
- 点击文件预览内容

## 实现细节

### Store 结构

```javascript
// stores/workspace.js
export const useWorkspaceStore = defineStore('workspace', () => {
  const folders = ref([])      // 工作区文件夹列表
  const activeFileId = ref(null)  // 当前选中文件
  const fileTree = ref([])     // 文件树数据

  function addFolder(folder) { /* ... */ }
  function removeFolder(folderId) { /* ... */ }
  function selectFile(fileId) { /* ... */ }

  return { folders, activeFileId, fileTree, addFolder, removeFolder, selectFile }
})
```

### Electron API

```javascript
// electron/preload.js
contextBridge.exposeInMainWorld('electronAPI', {
  selectFolder: () => ipcRenderer.invoke('select-folder'),
  readDir: (path) => ipcRenderer.invoke('read-dir', path),
  readFile: (path) => ipcRenderer.invoke('read-file', path),
})
```

### 持久化

使用 `pinia-plugin-persistedstate` 持久化 `folders` 数据：

```javascript
persist: {
  key: 'workspace',
  paths: ['folders']
}
```

## 组件

| 组件 | 路径 | 说明 |
|------|------|------|
| Sidebar | `components/Layout/Sidebar.vue` | 文件夹树展示 |
| MainLayout | `components/Layout/MainLayout.vue` | 布局容器 |

## 使用方式

1. 点击左侧栏顶部「添加文件夹」按钮
2. 在系统对话框中选择文件夹
3. 文件夹内容自动加载到文件树
4. 点击文件即可预览

## 注意事项

- 大型文件夹可能需要较长加载时间
- 仅支持文本文件预览（Markdown、代码等）
- 暂不支持文件夹实时监听（计划 v0.3）
