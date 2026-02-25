# 多轮对话上下文 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 修改 sendMessage 函数，将历史对话消息包含在 API 请求中，实现真正的多轮对话。

**Architecture:** 
- 修改 `sendMessage` 函数，构建包含历史消息的完整 messages 数组
- 保持 system prompt 在第一条
- 将当前会话的所有历史消息（除了刚添加的用户和助手消息）包含在请求中
- 如果启用 includeContext，仍然在最后一条用户消息中添加文档内容

**Tech Stack:** Vue 3, Pinia

---

### Task 1: 修改 sendMessage 函数以包含历史上下文

**Files:**
- Modify: `app/src/stores/agent.js`

**Step 1: 理解当前流程**

当前 `sendMessage` 执行顺序：
1. 添加用户消息
2. 添加空的助手消息
3. 发送 API 请求（只包含 system + 当前用户消息）

**Step 2: 修改消息构建逻辑**

需要：
- 在添加新消息之前，获取当前的历史消息
- 构建 messages 数组：[system, ...历史消息, 当前用户消息（含上下文）]

**修改后的 sendMessage 函数：**

```javascript
async function sendMessage(userContent, includeContext = false) {
  isLoading.value = true
  error.value = null

  // 在添加新消息前获取历史消息
  const historyMessages = messages.value.map(m => ({
    role: m.role,
    content: m.content
  }))

  addMessage('user', userContent)
  const assistantMessage = addMessage('assistant', '')
  updateMessage(assistantMessage.id, { typing: true, loading: true })

  try {
    const documentStore = useDocumentStore()
    let context = ''

    if (includeContext && documentStore.currentFile) {
      context = `\n\n当前文档内容：\n${documentStore.content}`
    }

    // 构建完整的 messages 数组
    const apiMessages = [
      { role: 'system', content: '你是一个有用的助手。请用 Markdown 格式回复。' },
      ...historyMessages,
      { role: 'user', content: userContent + context }
    ]

    const api = createLlmApi(llmConfig.value.baseUrl, llmConfig.value.apiKey)
    const request = api.post('/chat/completions', {
      model: llmConfig.value.model,
      messages: apiMessages,
      stream: true,
    })

    updateMessage(assistantMessage.id, { loading: false })
    let fullContent = ''

    for await (const chunk of request.stream()) {
      if (chunk.error) {
        continue
      }

      if (chunk.result) {
        const delta = chunk.result.choices?.[0]?.delta?.content
        if (delta) {
          fullContent += delta
          updateMessage(assistantMessage.id, { content: fullContent })
        }
      }
    }

    updateMessage(assistantMessage.id, { typing: false })
  } catch (err) {
    error.value = err.message
    updateMessage(assistantMessage.id, {
      content: `抱歉，发生了错误：${err.message}`,
      typing: false,
      loading: false,
    })
  } finally {
    isLoading.value = false
  }
}
```

---

### Task 2: 测试功能

**Files:**
- Manual Testing

**Step 1: 启动开发服务器**

```bash
cd app
npm run dev
```

**Step 2: 测试多轮对话**

1. 发送第一条消息："你好，我叫小明"
2. 发送第二条消息："我叫什么名字？"
3. 验证 AI 能记住之前的对话内容

---

### Task 3: 更新文档

**Files:**
- Modify: `docs/roadmap.md`

将「多轮对话上下文」标记为 ✅ 已完成，并在已完成部分添加说明。
