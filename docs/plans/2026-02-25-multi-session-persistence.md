# 多会话持久化 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现支持多会话的对话历史持久化，使用良好的存储抽象层，便于后续切换到文件系统或 SQLite。

**Architecture:** 
- Repository 模式抽象存储层，定义统一的 SessionRepository 接口
- 先实现 LocalStorageRepository，后续可轻松扩展 FileRepository/SQLiteRepository
- Agent Store 依赖 Repository 接口，不直接依赖具体存储实现
- 支持会话创建、切换、删除、重命名等完整功能

**Tech Stack:** Vue 3, Pinia, localStorage (初期), 策略模式

---

## 数据模型定义

### Session 接口
```javascript
interface Session {
  id: string              // UUID
  title: string           // 会话标题
  createdAt: string       // ISO 时间戳
  updatedAt: string       // ISO 时间戳
  messages: Message[]     // 消息列表
}

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  typing: boolean
  isMarkdown: boolean
  loading?: boolean
}
```

---

## 任务列表

### Task 1: 创建存储抽象层 (Repository 接口)

**Files:**
- Create: `app/src/repositories/SessionRepository.js` (接口定义)
- Create: `app/src/repositories/LocalStorageSessionRepository.js` (localStorage 实现)

**Step 1: 创建 Repository 接口文件**

```javascript
// app/src/repositories/SessionRepository.js

export class SessionRepository {
  async getAll() { throw new Error('Not implemented') }
  async getById(id) { throw new Error('Not implemented') }
  async create(session) { throw new Error('Not implemented') }
  async update(id, updates) { throw new Error('Not implemented') }
  async delete(id) { throw new Error('Not implemented') }
}
```

**Step 2: 创建 LocalStorage 实现**

```javascript
// app/src/repositories/LocalStorageSessionRepository.js
import { SessionRepository } from './SessionRepository'

const STORAGE_KEY = 'qbase-sessions'

export class LocalStorageSessionRepository extends SessionRepository {
  constructor() {
    super()
    this._initStorage()
  }

  _initStorage() {
    if (!localStorage.getItem(STORAGE_KEY)) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify([]))
    }
  }

  _getAllSessions() {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
  }

  _saveSessions(sessions) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions))
  }

  async getAll() {
    return this._getAllSessions()
  }

  async getById(id) {
    const sessions = this._getAllSessions()
    return sessions.find(s => s.id === id) || null
  }

  async create(session) {
    const sessions = this._getAllSessions()
    sessions.push(session)
    this._saveSessions(sessions)
    return session
  }

  async update(id, updates) {
    const sessions = this._getAllSessions()
    const index = sessions.findIndex(s => s.id === id)
    if (index !== -1) {
      sessions[index] = { ...sessions[index], ...updates, updatedAt: new Date().toISOString() }
      this._saveSessions(sessions)
      return sessions[index]
    }
    return null
  }

  async delete(id) {
    const sessions = this._getAllSessions()
    const filtered = sessions.filter(s => s.id !== id)
    this._saveSessions(filtered)
  }
}
```

**Step 3: 验证文件创建成功**

---

### Task 2: 重构 Agent Store 以支持多会话

**Files:**
- Modify: `app/src/stores/agent.js`

**Step 1: 完全重写 agent.js**

```javascript
import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { useDocumentStore } from './document'
import { createLlmApi } from '@/utils/api'
import { LocalStorageSessionRepository } from '@/repositories/LocalStorageSessionRepository'

function generateId() {
  const array = new Uint8Array(16)
  crypto.getRandomValues(array)
  array[6] = (array[6] & 0x0f) | 0x40
  array[8] = (array[8] & 0x3f) | 0x80
  return [...array]
    .map((b, i) =>
      [4, 6, 8, 10].includes(i) ? '-' + b.toString(16).padStart(2, '0') : b.toString(16).padStart(2, '0')
    )
    .join('')
}

function generateSessionTitle(firstMessage) {
  const maxLength = 30
  const content = firstMessage || '新对话'
  return content.length > maxLength ? content.slice(0, maxLength) + '...' : content
}

export const useAgentStore = defineStore(
  'agent',
  () => {
    const repository = new LocalStorageSessionRepository()
    
    const sessions = ref([])
    const currentSessionId = ref(null)
    const isLoading = ref(false)
    const error = ref(null)

    const llmConfig = ref({
      type: 'openai',
      baseUrl: 'https://api.openai.com/v1',
      apiKey: '',
      model: 'gpt-3.5-turbo',
    })

    const currentSession = computed(() => {
      return sessions.value.find(s => s.id === currentSessionId.value) || null
    })

    const messages = computed(() => {
      return currentSession.value?.messages || []
    })

    async function loadSessions() {
      sessions.value = await repository.getAll()
      if (sessions.value.length === 0) {
        await createSession()
      } else if (!currentSessionId.value) {
        currentSessionId.value = sessions.value[0].id
      }
    }

    async function createSession() {
      const session = {
        id: generateId(),
        title: '新对话',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        messages: [],
      }
      await repository.create(session)
      sessions.value.push(session)
      currentSessionId.value = session.id
      return session
    }

    async function switchSession(sessionId) {
      if (sessions.value.find(s => s.id === sessionId)) {
        currentSessionId.value = sessionId
      }
    }

    async function deleteSession(sessionId) {
      await repository.delete(sessionId)
      const index = sessions.value.findIndex(s => s.id === sessionId)
      if (index !== -1) {
        sessions.value.splice(index, 1)
        if (currentSessionId.value === sessionId) {
          if (sessions.value.length > 0) {
            currentSessionId.value = sessions.value[0].id
          } else {
            await createSession()
          }
        }
      }
    }

    async function renameSession(sessionId, newTitle) {
      await repository.update(sessionId, { title: newTitle })
      const session = sessions.value.find(s => s.id === sessionId)
      if (session) {
        session.title = newTitle
      }
    }

    function addMessage(role, content) {
      if (!currentSession.value) return
      
      const message = {
        id: generateId(),
        role,
        content,
        timestamp: new Date().toISOString(),
        typing: false,
        isMarkdown: true,
      }
      currentSession.value.messages.push(message)
      
      if (currentSession.value.messages.length === 1 && role === 'user') {
        const title = generateSessionTitle(content)
        renameSession(currentSessionId.value, title)
      }
      
      _saveCurrentSession()
      return message
    }

    function updateMessage(id, updates) {
      if (!currentSession.value) return
      const index = currentSession.value.messages.findIndex((m) => m.id === id)
      if (index !== -1) {
        currentSession.value.messages[index] = { 
          ...currentSession.value.messages[index], 
          ...updates 
        }
        _saveCurrentSession()
      }
    }

    function clearMessages() {
      if (!currentSession.value) return
      currentSession.value.messages = []
      error.value = null
      _saveCurrentSession()
    }

    function _saveCurrentSession() {
      if (currentSession.value) {
        repository.update(currentSessionId.value, {
          messages: currentSession.value.messages,
        })
      }
    }

    function setLlmConfig(config) {
      llmConfig.value = { ...llmConfig.value, ...config }
    }

    async function sendMessage(userContent, includeContext = false) {
      isLoading.value = true
      error.value = null

      addMessage('user', userContent)
      const assistantMessage = addMessage('assistant', '')
      updateMessage(assistantMessage.id, { typing: true, loading: true })

      try {
        const documentStore = useDocumentStore()
        let context = ''

        if (includeContext && documentStore.currentFile) {
          context = `\n\n当前文档内容：\n${documentStore.content}`
        }

        const api = createLlmApi(llmConfig.value.baseUrl, llmConfig.value.apiKey)
        const request = api.post('/chat/completions', {
          model: llmConfig.value.model,
          messages: [
            { role: 'system', content: '你是一个有用的助手。请用 Markdown 格式回复。' },
            { role: 'user', content: userContent + context },
          ],
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

    loadSessions()

    return {
      sessions,
      currentSessionId,
      currentSession,
      messages,
      isLoading,
      error,
      llmConfig,
      loadSessions,
      createSession,
      switchSession,
      deleteSession,
      renameSession,
      addMessage,
      updateMessage,
      clearMessages,
      setLlmConfig,
      sendMessage,
    }
  },
  {
    persist: {
      key: 'qbase-agent',
      paths: ['llmConfig', 'currentSessionId'],
    },
  },
)
```

**Step 2: 更新 persist 配置，只持久化 llmConfig 和 currentSessionId**

---

### Task 3: 创建会话列表侧边栏组件

**Files:**
- Create: `app/src/components/Layout/SessionSidebar.vue`

**Step 1: 创建 SessionSidebar 组件**

```vue
<template>
  <div class="session-sidebar">
    <div class="sidebar-header">
      <span>对话历史</span>
      <el-button size="small" circle @click="handleNewSession">
        <el-icon><Plus /></el-icon>
      </el-button>
    </div>
    <div class="session-list">
      <div
        v-for="session in agentStore.sessions"
        :key="session.id"
        :class="['session-item', { active: agentStore.currentSessionId === session.id }]"
        @click="handleSwitchSession(session.id)"
      >
        <div class="session-title">{{ session.title }}</div>
        <div class="session-date">{{ formatDate(session.updatedAt) }}</div>
        <el-button
          size="small"
          circle
          class="delete-btn"
          @click.stop="handleDeleteSession(session.id)"
        >
          <el-icon><Delete /></el-icon>
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Plus, Delete } from '@element-plus/icons-vue'
import { useAgentStore } from '@/stores/agent'

const agentStore = useAgentStore()

function formatDate(isoString) {
  const date = new Date(isoString)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  return date.toLocaleDateString('zh-CN')
}

function handleNewSession() {
  agentStore.createSession()
}

function handleSwitchSession(sessionId) {
  agentStore.switchSession(sessionId)
}

function handleDeleteSession(sessionId) {
  agentStore.deleteSession(sessionId)
}
</script>

<style scoped>
.session-sidebar {
  width: 200px;
  border-right: 1px solid var(--el-border-color);
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color-page);
}

.sidebar-header {
  padding: 12px 16px;
  font-weight: 600;
  font-size: 14px;
  color: var(--el-text-color-secondary);
  border-bottom: 1px solid var(--el-border-color-lighter);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.session-item {
  padding: 10px 12px;
  margin-bottom: 4px;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  transition: background 0.2s;
}

.session-item:hover {
  background: var(--el-fill-color-light);
}

.session-item.active {
  background: var(--el-color-primary-light-9);
}

.session-title {
  font-size: 13px;
  color: var(--el-text-color-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding-right: 24px;
}

.session-date {
  font-size: 11px;
  color: var(--el-text-color-tertiary);
  margin-top: 4px;
}

.delete-btn {
  position: absolute;
  right: 4px;
  top: 50%;
  transform: translateY(-50%);
  opacity: 0;
  transition: opacity 0.2s;
}

.session-item:hover .delete-btn {
  opacity: 1;
}
</style>
```

---

### Task 4: 重构 AgentPanel 以集成会话列表

**Files:**
- Modify: `app/src/components/Layout/AgentPanel.vue`

**Step 1: 更新 AgentPanel 组件**

```vue
<template>
  <div class="agent-panel">
    <SessionSidebar />
    <div class="chat-area">
      <div class="panel-header">
        <span>{{ agentStore.currentSession?.title || 'AI 助手' }}</span>
        <div class="header-actions">
          <el-button size="small" circle @click="showConfig = true">
            <el-icon><Setting /></el-icon>
          </el-button>
          <el-button size="small" circle @click="handleClear">
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
      </div>
      <div class="panel-content">
        <BubbleList
          v-if="agentStore.messages.length > 0"
          :list="bubbleList"
          :max-height="maxHeight"
          ref="bubbleListRef"
        />
        <el-empty v-else description="开始对话吧">
          <template #image>
            <el-icon :size="80"><ChatDotRound /></el-icon>
          </template>
        </el-empty>
      </div>
      <div class="panel-footer">
        <div class="context-toggle">
          <el-checkbox v-model="includeContext" size="small">包含当前文档</el-checkbox>
        </div>
        <Sender
          v-model="inputValue"
          :loading="agentStore.isLoading"
          placeholder="输入消息..."
          @submit="handleSubmit"
        />
      </div>
      <LlmConfigDialog v-model="showConfig" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { Setting, Delete, ChatDotRound } from '@element-plus/icons-vue'
import { BubbleList, Sender } from 'vue-element-plus-x'
import { useAgentStore } from '@/stores/agent'
import LlmConfigDialog from '../LlmConfigDialog.vue'
import SessionSidebar from './SessionSidebar.vue'

const agentStore = useAgentStore()

const bubbleListRef = ref(null)
const inputValue = ref('')
const showConfig = ref(false)
const includeContext = ref(false)

const maxHeight = 'calc(100vh - 300px)'

const bubbleList = computed(() => {
  return agentStore.messages.map((msg) => ({
    content: msg.content,
    placement: msg.role === 'user' ? 'end' : 'start',
    loading: msg.loading,
    typing: msg.typing,
    isMarkdown: msg.isMarkdown,
    avatarIcon: msg.role === 'user' ? 'User' : 'ChatDotRound',
  }))
})

function handleSubmit() {
  if (!inputValue.value.trim()) return
  const content = inputValue.value
  inputValue.value = ''
  agentStore.sendMessage(content, includeContext.value)
  nextTick(() => {
    bubbleListRef.value?.scrollToBottom()
  })
}

function handleClear() {
  agentStore.clearMessages()
}
</script>

<style scoped>
.agent-panel {
  width: 45%;
  min-width: 450px;
  border-left: 1px solid var(--el-border-color);
  display: flex;
  flex-direction: row;
  overflow: hidden;
}

.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  padding: 12px 16px;
  font-weight: 600;
  font-size: 14px;
  color: var(--el-text-color-secondary);
  border-bottom: 1px solid var(--el-border-color-lighter);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.panel-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.panel-content :deep(.el-empty) {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.panel-footer {
  padding: 12px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.context-toggle {
  margin-bottom: 8px;
}
</style>
```

---

### Task 5: 测试验证

**测试步骤:**
1. 运行 `npm run dev` 启动开发服务器
2. 验证可以创建新会话
3. 验证可以切换会话
4. 验证发送消息后会话标题自动生成
5. 验证可以删除会话
6. 刷新页面，验证会话数据正确持久化
7. 验证 LLM 配置仍然正常工作

---

## 文件结构变更总结

```
app/src/
├── repositories/              # 新建目录
│   ├── SessionRepository.js          # 抽象接口
│   └── LocalStorageSessionRepository.js  # localStorage 实现
├── stores/
│   └── agent.js              # 完全重构
└── components/Layout/
    ├── AgentPanel.vue        # 更新，集成侧边栏
    └── SessionSidebar.vue    # 新建会话列表组件
```

---

## 后续扩展路径

当需要切换到文件系统或 SQLite 时，只需：

1. 创建新的 Repository 实现（如 `FileSessionRepository.js`）
2. 修改 `agent.js` 中初始化 repository 的那一行
3. 无需改动任何其他代码

---

## 风险与注意事项

1. **localStorage 容量限制**: 约 5-10MB，大量消息可能超出限制（后续版本迁移到文件系统）
2. **数据迁移**: 确保现有用户的消息能平滑迁移
3. **性能**: 消息量大时考虑分页加载（v0.4+）
