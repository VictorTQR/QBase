<script setup>
import { ref } from 'vue'
import { useUiStore } from '@/stores/ui'
import PanelHeader from '@/components/shared/PanelHeader.vue'
import PanelNavSidebar from './PanelNavSidebar.vue'
import ChatModule from '@/components/chat/ChatModule.vue'
import FlashcardModule from '@/components/flashcard/FlashcardModule.vue'
import MindmapModule from '@/components/generate/MindmapModule.vue'
import SummaryModule from '@/components/generate/SummaryModule.vue'
import LlmConfigDialog from '../LlmConfigDialog.vue'

const uiStore = useUiStore()
const showConfig = ref(false)

const handleModuleChange = (moduleId) => {
  uiStore.setActiveModule(moduleId)
}

const handleSettings = () => {
  showConfig.value = true
}

const handleMinimize = () => {
  uiStore.toggleAgentPanel()
}

const renderModule = () => {
  switch (uiStore.activeModule) {
    case 'chat':
      return ChatModule
    case 'flashcard':
      return FlashcardModule
    case 'mindmap':
      return MindmapModule
    case 'summary':
      return SummaryModule
    default:
      return ChatModule
  }
}
</script>

<template>
  <div class="agent-panel">
    <PanelHeader @settings="handleSettings" @minimize="handleMinimize" />
    <div class="panel-body">
      <div class="panel-content">
        <transition name="fade" mode="out-in">
          <component :is="renderModule()" :key="uiStore.activeModule" />
        </transition>
      </div>
      <PanelNavSidebar :active-module="uiStore.activeModule" @change="handleModuleChange" />
    </div>
    <LlmConfigDialog v-model="showConfig" />
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
