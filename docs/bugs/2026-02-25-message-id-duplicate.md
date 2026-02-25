# 消息 ID 重复 Bug 修复

**日期**: 2026-02-25
**影响版本**: v0.2
**状态**: ✅ 已修复

## 问题描述

测试 AI 对话功能时发现：
- 用户消息发送完成后，AI 返回的消息占位气泡能正常生成
- 但实际渲染的 AI 消息内容错误地显示在用户消息中

## 问题分析

### 根本原因

在 `app/src/stores/agent.js` 的 `addMessage` 函数中：

```javascript
function addMessage(role, content) {
  const message = {
    id: Date.now().toString(),  // 问题在这里！
    role,
    content,
    // ...
  }
}
```

使用 `Date.now().toString()` 作为消息 ID，当快速连续添加两条消息时（用户消息和 AI 消息），由于 `Date.now()` 只精确到毫秒，可能会**生成相同的 ID**。

### 问题复现流程

1. 用户发送消息 → 调用 `addMessage('user', content)` → 生成 ID: `1740464000000`
2. 立即添加 AI 占位消息 → 调用 `addMessage('assistant', '')` → 生成 ID: `1740464000000`（同一毫秒）
3. 当调用 `updateMessage(assistantMessage.id, { content: ... })` 时，由于两个消息 ID 相同，会错误地更新用户消息

## 修复方案

### 选择的方案：Web Crypto API 生成 UUID v4

使用浏览器原生的 `crypto.getRandomValues()` 生成标准的 UUID v4，无需安装额外依赖。

### 修改内容

**文件**: `app/src/stores/agent.js`

**新增函数**:

```javascript
function generateId() {
  const array = new Uint8Array(16)
  crypto.getRandomValues(array)
  array[6] = (array[6] & 0x0f) | 0x40  // UUID v4
  array[8] = (array[8] & 0x3f) | 0x80  // UUID variant
  return [...array]
    .map((b, i) =>
      [4, 6, 8, 10].includes(i) ? '-' + b.toString(16).padStart(2, '0') : b.toString(16).padStart(2, '0')
    )
    .join('')
}
```

**修改 `addMessage` 函数**:

```javascript
function addMessage(role, content) {
  const message = {
    id: generateId(),  // 使用 UUID 而不是 Date.now()
    role,
    content,
    timestamp: new Date().toISOString(),
    typing: false,
    isMarkdown: true,
  }
  messages.value.push(message)
  return message
}
```

## 验证

修复后：
- 每条消息都有唯一的 UUID（如：`550e8400-e29b-41d4-a716-446655440000`）
- AI 消息正确显示在自己的气泡中
- 用户消息和 AI 消息不再混淆

## 技术细节

### UUID v4 格式

```
xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
│       │    │    │    │
│       │    │    │    └─ 随机十六进制
│       │    │    └────── y 为 8,9,a,b
│       │    └─────────── 4 表示 UUID v4
│       └──────────────── 随机十六进制
└──────────────────────── 随机十六进制
```

### 其他考虑过的方案

| 方案 | 优点 | 缺点 |
|------|------|------|
| `uuid` npm 包 | 标准、可靠 | 需要安装依赖 |
| 时间戳+随机数 | 简单 | 非标准 UUID |
| 自增计数器 | 简单 | 页面刷新后重置 |

## 相关文件

- 修复文件: [agent.js](../../app/src/stores/agent.js)
- 实施报告: [v0.2-complete.md](../implementation/v0.2-complete.md)
