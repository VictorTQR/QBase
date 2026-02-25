# AI 助手

**状态**: ✅ 已完成
**版本**: v0.2
**更新日期**: 2026-02-25

## 功能概述

AI 助手功能提供基于 LLM 的智能对话能力，支持基于当前文档的上下文问答。

## 核心功能

### 对话交互

- 流式响应（打字效果）
- Markdown 渲染回复
- 对话历史管理

### LLM 配置

- OpenAI 兼容 API
- Ollama 本地模型
- 自定义 Base URL

### 文档上下文

- 可选择包含当前文档内容
- 基于文档的智能问答

## 实现细节

### Store 结构

```javascript
// stores/agent.js
export const useAgentStore = defineStore('agent', () => {
  const messages = ref([])
  const llmConfig = ref({
    type: 'openai',
    baseUrl: 'https://api.openai.com/v1',
    apiKey: '',
    model: 'gpt-4o-mini'
  })
  const isLoading = ref(false)

  function addMessage(role, content) { /* ... */ }
  function updateMessage(id, updates) { /* ... */ }
  async function sendMessage(content, options) { /* ... */ }
  function clearMessages() { /* ... */ }

  return { messages, llmConfig, isLoading, addMessage, updateMessage, sendMessage, clearMessages }
})
```

### 消息数据结构

```javascript
{
  id: 'uuid-v4',           // 唯一标识
  role: 'user' | 'assistant',
  content: '消息内容',
  timestamp: '2026-02-25T10:00:00.000Z',
  typing: false,           // 是否正在打字
  isMarkdown: true         // 是否 Markdown 格式
}
```

### 流式请求处理

使用原生 `fetch` API 处理 SSE 流式响应：

```javascript
async function sendMessage(content, options = {}) {
  const response = await fetch(`${llmConfig.value.baseUrl}/chat/completions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${llmConfig.value.apiKey}`
    },
    body: JSON.stringify({
      model: llmConfig.value.model,
      messages: [...messages.value, { role: 'user', content }],
      stream: true
    })
  })

  const reader = response.body.getReader()
  const decoder = new TextDecoder()

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    const chunk = decoder.decode(value)
    // 解析 SSE 数据并更新消息
  }
}
```

### 持久化

```javascript
persist: {
  key: 'agent',
  paths: ['llmConfig']
}
```

## 组件

| 组件 | 路径 | 说明 |
|------|------|------|
| AgentPanel | `components/Layout/AgentPanel.vue` | 对话面板 |
| LlmConfigDialog | `components/LlmConfigDialog.vue` | LLM 配置对话框 |

### Element-Plus-X 组件

- `BubbleList` - 对话气泡列表
- `Sender` - 输入框
- `XMarkdown` - Markdown 渲染（用于 AI 回复）

## 配置选项

### OpenAI 兼容 API

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| Base URL | API 端点 | `https://api.openai.com/v1` |
| API Key | 认证密钥 | - |
| Model | 模型名称 | `gpt-4o-mini` |

### Ollama 本地模型

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| Base URL | Ollama 端点 | `http://localhost:11434/v1` |
| Model | 模型名称 | `llama3` |

## 使用方式

1. 点击右侧面板配置按钮
2. 填写 LLM 配置信息
3. 在输入框中输入问题
4. 可勾选「包含当前文档」获取上下文
5. 发送并等待流式响应

## 已知问题

- [ ] 对话历史未持久化（计划 v0.3）
- [ ] 不支持多轮对话上下文（计划 v0.3）
- [ ] 不支持图片输入（计划 v0.4）

## 相关文档

- [消息 ID 重复 Bug 修复](../bugs/2026-02-25-message-id-duplicate.md)
