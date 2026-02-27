# 工作区管理功能完善设计方案

**日期**: 2026-02-27  
**版本**: v0.5.x  
**状态**: 🔄 进行中

## 一、概述

本次改进针对 QBase 工作区管理功能的基础完善，包括移除文件夹 UI、按需加载文件树、状态管理优化等核心功能。

## 二、功能范围

| 功能项 | 优先级 | 说明 |
|--------|--------|------|
| 1. 移除文件夹 UI | 高 | 在侧边栏文件夹节点添加右键菜单 |
| 2. 确认弹窗 | 高 | 使用 Element Plus ElMessageBox 确认删除 |
| 3. 按需加载文件树 | 高 | 使用 Tree 组件 lazy 模式，展开时动态加载 |
| 4. 修复 refreshFileTree | 中 | 完善 Store 中的空实现 |
| 5. 重复文件夹检测 | 中 | 添加文件夹时检查路径是否已存在 |
| 6. 清理无用状态 | 低 | 移除或整合未使用的 fileTree 状态 |

## 三、技术方案

### 3.1 文件树按需加载

**方案**: 使用 Element Plus Tree 组件的 `lazy` 模式

**关键配置**:
```vue
<el-tree
  :data="treeData"
  :props="treeProps"
  lazy
  :load="loadNode"
  node-key="id"
  @node-contextmenu="handleContextMenu"
/>
```

### 3.2 右键菜单设计

使用 `@node-contextmenu` 事件 + `el-dropdown` 或浮动菜单：
- 仅对根文件夹节点显示「移除」选项
- 子文件夹不显示移除选项

### 3.3 Store 优化

**workspace.js 修改**:
- `addFolder()`: 添加路径重复检测
- `refreshFileTree()`: 发出事件供组件监听
- 移除未使用的 `fileTree` 状态

## 四、文件修改清单

| 文件 | 修改类型 | 说明 |
|------|----------|------|
| `app/src/stores/workspace.js` | 重构 | 完善方法、添加检测、清理状态 |
| `app/src/components/Layout/Sidebar.vue` | 重构 | 实现 lazy 加载、右键菜单、删除确认 |

## 五、验收标准

- [ ] 可以通过右键菜单移除工作区文件夹
- [ ] 移除前有确认弹窗提示
- [ ] 文件树支持无限层级，展开时动态加载
- [ ] 添加重复路径文件夹时有提示
- [ ] refreshFileTree 能正常工作
- [ ] 现有功能不受影响
