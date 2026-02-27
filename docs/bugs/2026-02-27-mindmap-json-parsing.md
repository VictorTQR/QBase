# 思维导图 JSON 解析错误修复

**日期**: 2026-02-27
**问题类型**: Bug 修复
**状态**: ✅ 已解决

## 问题描述

测试思维导图生成功能时，发现 LLM 能够正常返回响应，但在渲染时提示"解析错误"。

### 错误现象

- LLM 请求成功
- 控制台显示 `Failed to parse mindmap JSON`
- UI 显示错误信息："思维导图生成失败：无法解析响应格式"

## 问题根因

### 1. JSON 解析逻辑缺陷

在 `app/src/stores/agent.js` 的 `generateMindmap` 方法中：

```javascript
// 问题代码
mindmap = JSON.parse(responseText)
```

直接对 LLM 的完整响应进行解析，但 LLM 经常返回包含额外文本的响应：

```
当然，这是为您生成的思维导图：

```json
{
  "title": "...",
  "nodes": [...]
}
```
```

### 2. 缺少数据验证

解析后没有验证数据结构的正确性，导致后续渲染可能出错。

### 3. 调试信息不足

没有输出原始响应，难以定位问题。

## 修复方案

### 1. 修复 JSON 提取逻辑

参考 `generateFlashcards` 的实现，添加正则表达式提取 JSON：

```javascript
// 修复后的代码
const jsonMatch = responseText.match(/\{[\s\S]*\}/)
if (jsonMatch) {
  mindmap = JSON.parse(jsonMatch[0])
} else {
  mindmap = JSON.parse(responseText)
}
```

### 2. 添加数据验证

在 `MindmapGenerator.vue` 中添加 `validateMindmap()` 函数：

```javascript
function validateMindmap(mindmap) {
  if (!mindmap) return { valid: false, reason: '数据为空' }
  if (!mindmap.title) return { valid: false, reason: '缺少 title 字段' }
  if (!Array.isArray(mindmap.nodes)) return { valid: false, reason: 'nodes 不是数组' }
  // ... 更多验证
}
```

### 3. 增强调试能力

- 添加 `console.log` 输出 LLM 原始响应
- 添加可折叠的调试面板显示原始 JSON 数据

## 修改文件列表

| 文件 | 修改内容 |
|------|---------|
| `app/src/stores/agent.js` | 修复 `generateMindmap()` 的 JSON 解析逻辑 |
| `app/src/components/mindmap/MindmapGenerator.vue` | 添加数据验证和调试面板 |

## 关键代码变更

### agent.js:303-308

```javascript
try {
  const jsonMatch = responseText.match(/\{[\s\S]*\}/)
  if (jsonMatch) {
    mindmap = JSON.parse(jsonMatch[0])
  } else {
    mindmap = JSON.parse(responseText)
  }
} catch (parseErr) {
  console.error('Failed to parse mindmap JSON:', parseErr)
  console.error('Response text was:', responseText)
  throw new Error('思维导图生成失败：无法解析响应格式')
}
```

### MindmapGenerator.vue:15-50

新增验证函数和调试面板。

## 测试建议

1. 打开任意 Markdown 文档
2. 进入"思维导图"标签页
3. 点击"生成思维导图"
4. 查看浏览器控制台（F12）确认有原始响应输出
5. 如有问题，展开"调试信息"查看原始 JSON

## 后续优化建议

1. **更健壮的 JSON 提取**：支持多种 markdown 代码块格式
2. **备用解析策略**：当 JSON 解析失败时尝试其他方式
3. **提示词优化**：在 prompt 中更明确地要求只返回 JSON
