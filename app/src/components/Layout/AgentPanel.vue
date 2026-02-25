<template>
  <div class="agent-panel">
    <SessionSidebar />
    <div class="main-area">
      <div class="mode-tabs">
        <div
          class="mode-tab"
          :class="{ active: activeMode === 'chat' }"
          @click="activeMode = 'chat'"
        >
          <el-icon><ChatDotRound /></el-icon>
          <span>对话</span>
        </div>
        <div
          class="mode-tab"
          :class="{ active: activeMode === 'flashcard' }"
          @click="activeMode = 'flashcard'"
        >
          <el-icon><DocumentCopy /></el-icon>
          <span>闪卡</span>
        </div>
      </div>

      <div v-if="activeMode === 'chat'" class="chat-area">
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

      <FlashcardPanel v-else class="flashcard-area" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { Setting, Delete, ChatDotRound, DocumentCopy } from '@element-plus/icons-vue'
import { BubbleList, Sender } from 'vue-element-plus-x'
import { useAgentStore } from '@/stores/agent'
import LlmConfigDialog from '../LlmConfigDialog.vue'
import SessionSidebar from './SessionSidebar.vue'
import FlashcardPanel from '../flashcards/FlashcardPanel.vue'

const agentStore = useAgentStore()

const bubbleListRef = ref(null)
const inputValue = ref('')
const showConfig = ref(false)
const includeContext = ref(false)
const activeMode = ref('chat')

const maxHeight = 'calc(100vh - 350px)'

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

.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.mode-tabs {
  display: flex;
  border-bottom: 1px solid var(--el-border-color-lighter);
  background-color: var(--el-bg-color);
}

.mode-tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 12px 16px;
  font-size: 14px;
  color: var(--el-text-color-secondary);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}

.mode-tab:hover {
  color: var(--el-text-color-primary);
}

.mode-tab.active {
  color: var(--el-color-primary);
  border-bottom-color: var(--el-color-primary);
}

.chat-area,
.flashcard-area {
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
