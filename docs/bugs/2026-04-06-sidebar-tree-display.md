# 侧边栏文件树显示问题修复

**日期**: 2026-04-06
**状态**: ✅ 已修复
**影响版本**: v1.2
**修复版本**: v1.2.1

## 问题描述

左侧边栏的文件树没有按照树形结构显示文件，所有文件都显示在同一层级，没有体现出文件夹层级关系。

### 问题表现
- 文件树显示为扁平列表，而非层级结构
- 文件夹和子文件夹之间没有缩进效果
- 无法直观看出文件的目录层级关系

## 根本原因

### 问题 1: Windows 路径分隔符处理

在 Windows 系统上，后端返回的 `rel_path` 使用反斜杠 `\` 作为路径分隔符，但前端 `buildFileTree` 函数使用正斜杠 `/` 进行分割：

```javascript
// treeUtils.js - 错误代码
const parts = file.rel_path.split('/')  // Windows 路径 "folder\file.md" 分割失败
```

这导致整个路径被视为一个文件名，无法正确构建树形结构。

### 问题 2: 缩进样式被覆盖

在 `Sidebar.vue` 中，CSS 样式覆盖了 Element Plus 树形组件的默认缩进：

```css
/* Sidebar.vue - 错误样式 */
:deep(.el-tree-node__content) {
  padding: 0 !important;  /* 这行代码破坏了缩进效果 */
  height: auto !important;
}
```

## 修复方案

### 修复 1: 统一路径分隔符

在 `buildFileTree` 函数中，先将 Windows 路径分隔符统一转换为正斜杠：

```javascript
// treeUtils.js - 修复后
export function buildFileTree(files) {
  const tree = []
  const pathMap = {}

  files.forEach((file) => {
    // 统一处理 Windows 和 Unix 路径分隔符
    const normalizedPath = file.rel_path.replace(/\\/g, '/')
    const parts = normalizedPath.split('/')
    // ...
  })
}
```

### 修复 2: 恢复缩进样式

移除覆盖缩进的 CSS 代码：

```css
/* Sidebar.vue - 修复后 */
:deep(.el-tree-node__content) {
  height: auto !important;
}
```

## 修复文件

1. **文件**: `app/src/utils/treeUtils.js`
   - **函数**: `buildFileTree`
   - **修改**: 添加路径分隔符统一处理

2. **文件**: `app/src/components/Layout/Sidebar.vue`
   - **样式**: `:deep(.el-tree-node__content)`
   - **修改**: 移除 `padding: 0 !important`

## 修复效果

修复后：
1. 文件树按照正确的层级结构显示
2. 子文件夹和文件有适当的缩进，层级关系清晰可见
3. 支持 Windows 和 Unix 两种路径格式
