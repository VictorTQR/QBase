# 测试连接功能 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 LLM 配置对话框中添加测试连接功能，允许用户验证 LLM 配置是否正确。

**Architecture:** 
- 在 agent store 中添加 `testConnection` 函数，发送简单的测试请求
- 在 LlmConfigDialog 组件中调用该函数并显示结果
- 支持加载状态和成功/失败提示

**Tech Stack:** Vue 3, Pinia, Element Plus, hook-fetch

---

### Task 1: 在 agent store 中添加测试连接函数

**Files:**
- Modify: `app/src/stores/agent.js`

**Step 1: 实现 testConnection 函数**

在 `agent.js` 中添加 `testConnection` 异步函数，使用当前配置发送简单的测试请求。

添加位置：在 `setLlmConfig` 函数之后，`sendMessage` 函数之前。

**Step 2: 函数实现代码**

```javascript
async function testConnection() {
  try {
    const api = createLlmApi(llmConfig.value.baseUrl, llmConfig.value.apiKey)
    const request = api.post('/chat/completions', {
      model: llmConfig.value.model,
      messages: [
        { role: 'user', content: 'Hi' },
      ],
      stream: false,
      max_tokens: 5,
    })
    
    const response = await request.json()
    return { success: true, message: '连接成功！' }
  } catch (err) {
    return { success: false, message: `连接失败：${err.message}` }
  }
}
```

**Step 3: 导出 testConnection 函数**

在 store 的 return 对象中添加 `testConnection`。

---

### Task 2: 在 LlmConfigDialog 组件中实现测试功能

**Files:**
- Modify: `app/src/components/LlmConfigDialog.vue`

**Step 1: 添加响应式状态**

添加 `isTesting` 加载状态和消息提示相关逻辑。

**Step 2: 实现 handleTest 函数**

替换现有的 `handleTest` 函数，调用 store 的 `testConnection` 并显示结果。

**Step 3: 添加 UI 反馈**

- 测试时禁用按钮并显示加载状态
- 使用 Element Plus 的 ElMessage 显示成功/失败消息

**完整代码修改：**

```vue
<script setup>
import { ref, watch } from 'vue'
import { useAgentStore } from '@/stores/agent'
import { ElMessage } from 'element-plus'

// ... 现有代码 ...

const isTesting = ref(false)

async function handleTest() {
  if (!form.value.baseUrl || !form.value.model) {
    ElMessage.warning('请填写 Base URL 和 Model')
    return
  }
  
  isTesting.value = true
  try {
    // 临时使用表单中的配置进行测试
    const originalConfig = { ...agentStore.llmConfig }
    agentStore.setLlmConfig(form.value)
    
    const result = await agentStore.testConnection()
    
    // 恢复原始配置
    agentStore.setLlmConfig(originalConfig)
    
    if (result.success) {
      ElMessage.success(result.message)
    } else {
      ElMessage.error(result.message)
    }
  } catch (err) {
    ElMessage.error(`测试失败：${err.message}`)
  } finally {
    isTesting.value = false
  }
}

// ... 现有代码 ...
</script>
```

**Step 4: 更新模板中的按钮**

修改「测试连接」按钮，添加 loading 状态：

```vue
<el-button :loading="isTesting" @click="handleTest">测试连接</el-button>
```

---

### Task 3: 测试功能

**Files:**
- Manual Testing

**Step 1: 启动开发服务器**

```bash
cd app
npm run dev
```

**Step 2: 测试场景**

1. 打开 LLM 配置对话框
2. 不填写信息直接点击「测试连接」- 应显示警告
3. 填写正确配置并测试 - 应显示成功
4. 填写错误配置并测试 - 应显示错误

---

### Task 4: 更新文档

**Files:**
- Modify: `docs/roadmap.md`

将「测试连接功能」标记为 ✅ 已完成。
