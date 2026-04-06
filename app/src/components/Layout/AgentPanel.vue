<script setup>
import { ref } from 'vue'
import { useUiStore } from '@/stores/ui'
import PanelHeader from '@/components/shared/PanelHeader.vue'
import ChatModule from '@/components/chat/ChatModule.vue'
import FlashcardPanel from '@/components/flashcards/FlashcardPanel.vue'
import MindmapGenerator from '@/components/mindmap/MindmapGenerator.vue'
import SummaryGenerator from '@/components/summary/SummaryGenerator.vue'

const uiStore = useUiStore()

const agentTabs = [
  { id: 'chat', name: '对话', icon: '💬' },
  { id: 'flashcard', name: '闪卡', icon: '🃏' },
  { id: 'mindmap', name: '导图', icon: '🧠' },
  { id: 'summary', name: '摘要', icon: '📊' }
]
const activeTab = ref('chat')

const handleMinimize = () => {
  uiStore.toggleAgentPanel()
}
</script>

<template>
  <div class="agent-panel">
    <PanelHeader @minimize="handleMinimize" />
    <div class="agent-tabs">
      <div
        v-for="tab in agentTabs"
        :key="tab.id"
        class="agent-tab"
        :class="{ active: activeTab === tab.id }"
        @click="activeTab = tab.id"
      >
        <span>{{ tab.icon }}</span>
        <span>{{ tab.name }}</span>
      </div>
    </div>
    <div class="panel-body">
      <div class="panel-content">
        <transition name="fade" mode="out-in">
          <ChatModule v-if="activeTab === 'chat'" key="chat" />
          <FlashcardPanel v-else-if="activeTab === 'flashcard'" key="flashcard" />
          <MindmapGenerator v-else-if="activeTab === 'mindmap'" key="mindmap" />
          <SummaryGenerator v-else-if="activeTab === 'summary'" key="summary" />
        </transition>
      </div>
    </div>
  </div>
</template>

<style scoped>
.agent-panel {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: var(--el-bg-color);
  border-left: 1px solid var(--el-border-color-lighter);
}

.agent-tabs {
  display: flex;
  padding: 10px 12px;
  border-bottom: 1px solid var(--border-subtle);
  gap: 6px;
  background: var(--bg-secondary);
}

.agent-tab {
  flex: 1;
  padding: 8px 10px;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  background: transparent;
  transition: all var(--duration-base) var(--ease-out);
  border: 1px solid transparent;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: var(--text-secondary);
}

.agent-tab:hover {
  background: var(--bg-tertiary);
}

.agent-tab.active {
  background: var(--bg-primary);
  color: var(--primary-600);
  border-color: var(--primary-200);
  box-shadow: var(--shadow-sm);
}

.panel-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.panel-content {
  flex: 1;
  overflow: hidden;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
