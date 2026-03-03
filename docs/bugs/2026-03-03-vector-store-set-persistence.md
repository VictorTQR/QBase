# Bug 修复记录：Vector Store Set 持久化问题

**状态**: ✅ 已修复  
**发现日期**: 2026-03-03  
**修复日期**: 2026-03-03  
**影响版本**: v1.1 (向量搜索与索引集成)

## 问题描述

### 错误信息

```
TypeError: indexedFiles.value.has is not a function
    at Proxy.isFileIndexed (vector.js:99:33)
    at ParseDocumentsView.vue:126:61
    at Array.filter (<anonymous>)
```

### 复现步骤

1. 打开应用
2. 导航到解析管理页面
3. 点击「已解析文档」或「解析统计」标签
4. 页面报错并无法正常显示

## 问题分析

### 根本原因

Pinia 持久化插件无法正确处理 JavaScript 的 `Set` 对象。

**问题代码** (`app/src/stores/vector.js`):
```javascript
// 有问题的代码
const indexedFiles = ref(new Set())  // ❌ Set 不能被 Pinia 正确持久化

// 持久化配置
persist: {
  key: 'qbase-vector',
  paths: ['indexedFiles'],  // ❌ Set 无法正确序列化
}
```

### 技术细节

1. **Pinia 持久化机制**:
   - 使用 `JSON.stringify()` 序列化状态
   - 使用 `JSON.parse()` 反序列化状态
   - `Set` 对象无法被正确序列化

2. **问题表现**:
   - 初始加载时：`indexedFiles = new Set()` - 正常工作
   - 页面刷新后：`indexedFiles = {}` (普通对象) - `.has()` 方法不存在

3. **受影响的方法**:
   - `isFileIndexed(filePath)` - 调用 `.has()` 时报错
   - `markFileIndexed(filePath)` - 调用 `.add()` 时报错
   - `unmarkFileIndexed(filePath)` - 调用 `.delete()` 时报错
   - `clearAll()` - 调用 `.clear()` 时报错

## 修复方案

### 修复策略

将 `Set` 对象替换为普通对象 `{}`，使用对象属性来跟踪已索引文件。

### 修复代码

**修改前**:
```javascript
const indexedFiles = ref(new Set())

function isFileIndexed(filePath) {
  return indexedFiles.value.has(filePath)
}

function markFileIndexed(filePath) {
  indexedFiles.value.add(filePath)
}

function unmarkFileIndexed(filePath) {
  indexedFiles.value.delete(filePath)
}

async function clearAll() {
  const result = await VectorBackendApi.clearAllVectors()
  stats.value = null
  indexedFiles.value.clear()
  return result
}

// 在 indexDocument 中
indexedFiles.value.add(filePath)
```

**修改后**:
```javascript
const indexedFiles = ref({})

function isFileIndexed(filePath) {
  return !!indexedFiles.value[filePath]
}

function markFileIndexed(filePath) {
  indexedFiles.value[filePath] = true
}

function unmarkFileIndexed(filePath) {
  delete indexedFiles.value[filePath]
}

async function clearAll() {
  const result = await VectorBackendApi.clearAllVectors()
  stats.value = null
  indexedFiles.value = {}
  return result
}

// 在 indexDocument 中
indexedFiles.value[filePath] = true
```

### 额外修复

同时修复了另一个相关问题：
- **问题**: `workspace_id` 传递 `null` 导致后端 Pydantic 验证失败（422 错误）
- **修复**: 将 `workspace_id: null` 改为 `workspace_id: ""` (空字符串)

### 增强功能

添加了详细的错误日志：
- 前端：记录请求参数、响应数据、错误详情
- 帮助后续问题诊断

## 验证

### 测试清单

- [x] 已解析文档页面正常加载
- [x] 解析统计页面正常加载
- [x] 向量状态标签正确显示（已索引/未索引）
- [x] 单个文档索引功能正常
- [x] 批量索引功能正常
- [x] 页面刷新后状态正确恢复
- [x] 清空所有向量功能正常

### 结果

✅ 所有功能恢复正常，页面不再报错。

## 预防措施

### 代码规范

1. **避免在 Pinia 持久化中使用复杂对象**:
   - ✅ 使用普通对象 `{}`
   - ✅ 使用数组 `[]`
   - ❌ 避免使用 `Set`、`Map`、`Date` 等

2. **持久化数据验证**:
   - 初始化时检查数据类型
   - 提供默认值

3. **测试覆盖**:
   - 测试页面刷新后的状态恢复
   - 测试持久化数据的兼容性

### 相关文档

- [向量索引集成实施报告](../implementation/2026-03-03-vector-index-integration.md)
- [向量搜索前端实施报告](../implementation/2026-03-03-vector-search-frontend.md)

## 总结

这个 bug 是由于对 Pinia 持久化机制的理解不足导致的。通过将 `Set` 替换为普通对象，问题得到了完全解决。同时还增强了错误日志，便于未来的问题诊断。

**关键教训**: Pinia 持久化只支持 JSON 可序列化的简单数据类型。
