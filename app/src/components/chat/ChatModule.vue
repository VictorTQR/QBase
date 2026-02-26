<script setup>
import { ref, computed, nextTick, watch } from 'vue'
import { List, Delete, ChatDotRound } from '@element-plus/icons-vue'
import { BubbleList, Sender } from 'vue-element-plus-x'
import { useAgentStore } from '@/stores/agent'
import { useDocumentStore } from '@/stores/document'
import SessionSidebar from './SessionSidebar.vue'

const agentStore = useAgentStore()
const documentStore = useDocumentStore()

const inputValue = ref('')
const includeContext = ref(false)
const maxHeight = ref('calc(100vh - 350px)')
const showSessionSidebar = ref(true)
const bubbleListRef = ref(null)

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

const handleSubmit = async (content) => {
  if (!content.trim() || agentStore.isLoading) return
  await agentStore.sendMessage(content, includeContext.value)
  inputValue.value = ''
  nextTick(() => {
    bubbleListRef.value?.scrollToBottom()
  })
}

const handleClear = () => {
  agentStore.clearMessages()
}

watch(
  () => agentStore.messages.length,
  () => {
    nextTick(() => {
      bubbleListRef.value?.scrollToBottom()
    })
  },
)
</script>

<template>
  <div class="chat-module">
    <div class="chat-header">
      <el-button size="small" text @click="showSessionSidebar = !showSessionSidebar">
        <el-icon><List /></el-icon>
        会话
      </el-button>
      <span class="current-session-title">{{ agentStore.currentSession?.title || 'AI 助手' }}</span>
      <div class="header-actions">
        <el-button size="small" circle @click="handleClear">
          <el-icon><Delete /></el-icon>
        </el-button>
      </div>
    </div>

    <div class="chat-body">
      <SessionSidebar v-if="showSessionSidebar" />
      <div class="chat-content">
        <div class="messages-container">
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
        <div class="chat-footer">
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
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-module {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chat-header {
  height: 40px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.current-session-title {
  flex: 1;
  font-weight: 500;
  font-size: 13px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.chat-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.chat-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.messages-container {
  flex: 1;
  overflow: hidden;
  padding: 16px;
}

.messages-container :deep(.el-empty) {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chat-footer {
  padding: 12px 16px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.context-toggle {
  margin-bottom: 8px;
}
</style>
