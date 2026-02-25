import { ref } from 'vue'
import { defineStore } from 'pinia'
import { useDocumentStore } from './document'
import { createLlmApi } from '@/utils/api'

export const useAgentStore = defineStore(
  'agent',
  () => {
    const messages = ref([])
    const isLoading = ref(false)
    const error = ref(null)

    const llmConfig = ref({
      type: 'openai',
      baseUrl: 'https://api.openai.com/v1',
      apiKey: '',
      model: 'gpt-3.5-turbo',
    })

    function addMessage(role, content) {
      const message = {
        id: Date.now().toString(),
        role,
        content,
        timestamp: new Date().toISOString(),
        typing: false,
        isMarkdown: true,
      }
      messages.value.push(message)
      return message
    }

    function updateMessage(id, updates) {
      const index = messages.value.findIndex((m) => m.id === id)
      if (index !== -1) {
        messages.value[index] = { ...messages.value[index], ...updates }
      }
    }

    function clearMessages() {
      messages.value = []
      error.value = null
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

    return {
      messages,
      isLoading,
      error,
      llmConfig,
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
      paths: ['llmConfig'],
    },
  },
)
