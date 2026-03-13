# Element Plus Table 列宽塌陷问题修复

**日期**: 2026-03-13  
**状态**: ✅ 已修复  
**影响文件**: `app/src/components/parse/FileManagementView.vue`

## 问题描述

在解析管理的文件管理视图中，Element Plus 的 `el-table` 组件出现列宽塌陷问题：
- 使用 `width="8%"` 等百分比设置时，列宽无法正确应用
- 列宽塌陷为内容的最小宽度
- 表格布局混乱

## 问题原因

Element Plus 的 `el-table-column` 组件在解析 `width` 属性时，通常期望接收具体的像素值或数字。当直接传入百分比如 `width="8%"` 时，Element Plus 无法正确识别并应用该样式。

默认的 `table-layout="fixed"` 布局需要明确的像素宽度才能正确工作。

## 修复方案

### 1. 修改表格布局模式

将 `el-table` 的 `table-layout` 从默认的 `fixed` 改为 `auto`，并使用 `min-width` 替代 `width`。

### 2. 修复 Set 响应式问题

额外发现 `selectedFiles` 的响应式问题：`ref(new Set())` 包裹的 Set 对象，其 `add/delete` 操作不会触发 Vue 的响应式更新。

## 代码修改

### 修改 el-table 配置

```vue
<!-- 修改前 -->
<el-table :data="filteredFiles" style="width: 100%; min-width: 900px;">
  <el-table-column width="8%">
  ...

<!-- 修改后 -->
<el-table 
  :data="filteredFiles" 
  style="width: 100%; min-width: 900px;"
  table-layout="auto"
>
  <el-table-column min-width="8%">
  ...
```

### 修复 Set 响应式

```javascript
// 修改前
function toggleSelectAll() {
  if (selectAll.value) {
    filteredFiles.value.forEach(f => selectedFiles.value.add(f.id))
  } else {
    selectedFiles.value.clear()
  }
}

function toggleFileSelection(fileId) {
  if (selectedFiles.value.has(fileId)) {
    selectedFiles.value.delete(fileId)
  } else {
    selectedFiles.value.add(fileId)
  }
  selectAll.value = selectedFiles.value.size === filteredFiles.value.length
}

// 修改后
function toggleSelectAll() {
  if (selectAll.value) {
    selectedFiles.value = new Set(filteredFiles.value.map(f => f.id))
  } else {
    selectedFiles.value = new Set()
  }
}

function toggleFileSelection(fileId) {
  const newSet = new Set(selectedFiles.value)
  if (newSet.has(fileId)) {
    newSet.delete(fileId)
  } else {
    newSet.add(fileId)
  }
  selectedFiles.value = newSet
  selectAll.value = newSet.size === filteredFiles.value.length
}
```

### 移除 CSS 中的 table-layout 强制设置

```css
/* 修改前 */
.table-container :deep(.el-table) {
  table-layout: fixed;
  width: 100%;
}

/* 修改后 */
.table-container :deep(.el-table) {
  width: 100%;
}
```

## 关键修改点

| 修改项 | 说明 |
|--------|------|
| `min-width` 替代 `width` | Element Plus 的 `width` 在非像素值情况下行为不稳定，`min-width` 更可靠 |
| `table-layout="auto"` | 让浏览器根据内容或 `min-width` 比例自动分配列宽 |
| Set 重新赋值 | 通过创建新的 Set 实例触发 Vue 响应式更新 |

## 验证结果

- ✅ 表格列宽正确按比例分配
- ✅ 复选框选择功能响应式正常
- ✅ 表格布局稳定，不再塌陷

## 相关文档

- [Element Plus Table 文档](https://element-plus.org/zh-CN/component/table.html)
- [Vue 响应式基础](https://cn.vuejs.org/guide/essentials/reactivity-fundamentals.html)
