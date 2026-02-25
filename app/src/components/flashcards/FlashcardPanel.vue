<template>
  <div class="flashcard-panel">
    <div class="panel-header">
      <div class="tabs">
        <div
          class="tab"
          :class="{ active: flashcardStore.viewMode === 'generate' }"
          @click="flashcardStore.viewMode = 'generate'"
        >
          生成闪卡
        </div>
        <div
          class="tab"
          :class="{ active: flashcardStore.viewMode === 'list' }"
          @click="flashcardStore.viewMode = 'list'"
        >
          闪卡列表
        </div>
        <div
          v-if="flashcardStore.currentSet"
          class="tab"
          :class="{ active: flashcardStore.viewMode === 'view' }"
          @click="flashcardStore.viewMode = 'view'"
        >
          学习模式
        </div>
      </div>
    </div>

    <div class="panel-content">
      <FlashcardGenerator v-if="flashcardStore.viewMode === 'generate'" />
      <FlashcardSet v-else-if="flashcardStore.viewMode === 'list'" />
      <FlashcardViewer v-else-if="flashcardStore.viewMode === 'view'" />
    </div>
  </div>
</template>

<script setup>
import { useFlashcardStore } from '@/stores/flashcard'
import FlashcardGenerator from './FlashcardGenerator.vue'
import FlashcardSet from './FlashcardSet.vue'
import FlashcardViewer from './FlashcardViewer.vue'

const flashcardStore = useFlashcardStore()
</script>

<style scoped>
.flashcard-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: var(--el-bg-color-page);
}

.panel-header {
  border-bottom: 1px solid var(--el-border-color-lighter);
  background-color: var(--el-bg-color);
}

.tabs {
  display: flex;
  padding: 0 16px;
}

.tab {
  padding: 12px 16px;
  font-size: 14px;
  color: var(--el-text-color-secondary);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}

.tab:hover {
  color: var(--el-text-color-primary);
}

.tab.active {
  color: var(--el-color-primary);
  border-bottom-color: var(--el-color-primary);
}

.panel-content {
  flex: 1;
  overflow: hidden;
}
</style>
