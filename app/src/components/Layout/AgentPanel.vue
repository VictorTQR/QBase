<script setup>
import { useUiStore } from '@/stores/ui'
import PanelHeader from '@/components/shared/PanelHeader.vue'
import PanelNavSidebar from './PanelNavSidebar.vue'
import ChatModule from '@/components/chat/ChatModule.vue'
import FlashcardPanel from '@/components/flashcards/FlashcardPanel.vue'
import MindmapGenerator from '@/components/mindmap/MindmapGenerator.vue'
import SummaryGenerator from '@/components/summary/SummaryGenerator.vue'

const uiStore = useUiStore()

const handleModuleChange = (moduleId) => {
  uiStore.setActiveModule(moduleId)
}

const handleMinimize = () => {
  uiStore.toggleAgentPanel()
}

const renderModule = () => {
  switch (uiStore.activeModule) {
    case 'chat':
      return ChatModule
    case 'flashcard':
      return FlashcardPanel
    case 'mindmap':
      return MindmapGenerator
    case 'summary':
      return SummaryGenerator
    default:
      return ChatModule
  }
}
</script>

<template>
  <div class="agent-panel">
    <PanelHeader @minimize="handleMinimize" />
    <div class="panel-body">
      <div class="panel-content">
        <transition name="fade" mode="out-in">
          <component :is="renderModule()" :key="uiStore.activeModule" />
        </transition>
      </div>
      <PanelNavSidebar :active-module="uiStore.activeModule" @change="handleModuleChange" />
    </div>
  </div>
</template>

<style scoped>
.agent-panel {
  width: 45%;
  min-width: 450px;
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: var(--el-bg-color);
  border-left: 1px solid var(--el-border-color-lighter);
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
