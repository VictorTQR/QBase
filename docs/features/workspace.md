# 工作区管理

**状态**: ✅ 已完成
**版本**: v0.5.x
**更新日期**: 2026-02-27

## 功能概述

工作区管理功能允许用户添加和管理本地文件夹，构建个人知识库的文件索引。

## 核心功能

### 添加文件夹

- 通过 Electron API 打开系统文件夹选择对话框
- 重复路径检测，防止重复添加
- 操作成功/失败提示

### 移除文件夹

- 右键点击根文件夹显示菜单
- 确认弹窗防止误操作
- 从工作区列表中移除

### 文件树导航

- 树形展示文件夹结构
- 支持按需 lazy 加载（无限层级）
- 支持展开/折叠
- 手动刷新功能
- 点击文件预览内容

## 实现细节

### Store 结构

```javascript
// stores/workspace.js
export const useWorkspaceStore = defineStore('workspace', () => {
  const folders = ref([])          // 工作区文件夹列表
  const activeFileId = ref(null)    // 当前选中文件
  const needsRefresh = ref(false)    // 刷新标记

  function addFolder(folder) { /* 含重复检测 */ }
  function removeFolder(folderId) { /* ... */ }
  function refreshFileTree() { /* ... */ }
  function selectFile(fileId) { /* ... */ }

  return { folders, activeFileId, needsRefresh, addFolder, removeFolder, refreshFileTree, selectFile }
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

1. 点击顶部「添加文件夹」按钮
2. 在系统对话框中选择文件夹
3. 文件夹显示在左侧文件树中
4. 展开文件夹按需加载内容
5. 点击文件即可预览
6. 右键点击根文件夹可选择「移除文件夹」

## 注意事项

- 文件树采用按需加载，性能更优
- 支持无限层级文件夹
- 暂不支持文件夹实时监听（计划 v0.3）
