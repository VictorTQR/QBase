import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { useDocumentStore } from './document'
import { createLlmApi } from '@/utils/api'
import { generateFlashcardPrompt, generateMindmapPrompt, generateSummaryPrompt } from '@/utils/prompts'
import { LocalStorageSessionRepository } from '@/repositories/LocalStorageSessionRepository'

function generateId() {
  const array = new Uint8Array(16)
  crypto.getRandomValues(array)
  array[6] = (array[6] & 0x0f) | 0x40
  array[8] = (array[8] & 0x3f) | 0x80
  return [...array]
    .map((b, i) =>
      [4, 6, 8, 10].includes(i)
        ? '-' + b.toString(16).padStart(2, '0')
        : b.toString(16).padStart(2, '0'),
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
      return sessions.value.find((s) => s.id === currentSessionId.value) || null
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
      if (sessions.value.find((s) => s.id === sessionId)) {
        currentSessionId.value = sessionId
      }
    }

    async function deleteSession(sessionId) {
      await repository.delete(sessionId)
      const index = sessions.value.findIndex((s) => s.id === sessionId)
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
      const session = sessions.value.find((s) => s.id === sessionId)
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
          ...updates,
        }
        _saveCurrentSession()
      }
    }

    function clearMessages() {
      if (!currentSession.value) return
      currentSession.value.messages = []
      currentSession.value.title = '新对话'
      error.value = null
      _saveCurrentSession()
    }

    function _saveCurrentSession() {
      if (currentSession.value) {
        repository.update(currentSessionId.value, {
          messages: currentSession.value.messages,
          title: currentSession.value.title,
        })
      }
    }

    function setLlmConfig(config) {
      llmConfig.value = { ...llmConfig.value, ...config }
    }

    async function testConnection() {
      try {
        const api = createLlmApi(llmConfig.value.baseUrl, llmConfig.value.apiKey)
        const request = api.post('/chat/completions', {
          model: llmConfig.value.model,
          messages: [{ role: 'user', content: 'Hi' }],
          stream: false,
          max_tokens: 5,
        })

        await request.json()
        return { success: true, message: '连接成功！' }
      } catch (err) {
        return { success: false, message: `连接失败：${err.message}` }
      }
    }

    async function sendMessage(userContent, includeContext = false) {
      isLoading.value = true
      error.value = null

      const historyMessages = messages.value.map((m) => ({
        role: m.role,
        content: m.content,
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

        const apiMessages = [
          { role: 'system', content: '你是一个有用的助手。请用 Markdown 格式回复。' },
          ...historyMessages,
          { role: 'user', content: userContent + context },
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

    async function generateFlashcards(content, count = 10) {
      try {
        const prompt = generateFlashcardPrompt(content, count)
        const api = createLlmApi(llmConfig.value.baseUrl, llmConfig.value.apiKey)
        const request = api.post('/chat/completions', {
          model: llmConfig.value.model,
          messages: [{ role: 'user', content: prompt }],
          stream: false,
          temperature: 0.7,
        })

        const result = await request.json()
        const responseText = result.choices?.[0]?.message?.content || ''

        let flashcards = []
        try {
          const jsonMatch = responseText.match(/\[[\s\S]*\]/)
          if (jsonMatch) {
            flashcards = JSON.parse(jsonMatch[0])
          } else {
            flashcards = JSON.parse(responseText)
          }
        } catch (parseErr) {
          console.error('Failed to parse flashcards JSON:', parseErr)
          throw new Error('闪卡生成失败：无法解析响应格式')
        }

        return { success: true, flashcards }
      } catch (err) {
        return { success: false, error: err.message }
      }
    }

    async function generateMindmap(content) {
      try {
        const prompt = generateMindmapPrompt(content)
        const api = createLlmApi(llmConfig.value.baseUrl, llmConfig.value.apiKey)
        const request = api.post('/chat/completions', {
          model: llmConfig.value.model,
          messages: [{ role: 'user', content: prompt }],
          stream: false,
          temperature: 0.7,
        })

        const result = await request.json()
        const responseText = result.choices?.[0]?.message?.content || ''

        let mindmap = null
        try {
          mindmap = JSON.parse(responseText)
        } catch (parseErr) {
          console.error('Failed to parse mindmap JSON:', parseErr)
          throw new Error('思维导图生成失败：无法解析响应格式')
        }

        return { success: true, mindmap }
      } catch (err) {
        return { success: false, error: err.message }
      }
    }

    async function generateSummary(content) {
      try {
        const prompt = generateSummaryPrompt(content)
        const api = createLlmApi(llmConfig.value.baseUrl, llmConfig.value.apiKey)
        const request = api.post('/chat/completions', {
          model: llmConfig.value.model,
          messages: [{ role: 'user', content: prompt }],
          stream: false,
          temperature: 0.7,
        })

        const result = await request.json()
        const summary = result.choices?.[0]?.message?.content || ''

        return { success: true, summary }
      } catch (err) {
        return { success: false, error: err.message }
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
      testConnection,
      sendMessage,
      generateFlashcards,
      generateMindmap,
      generateSummary,
    }
  },
  {
    persist: {
      key: 'qbase-agent',
      paths: ['llmConfig', 'currentSessionId'],
    },
  },
)
