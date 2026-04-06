<template>
  <div class="content-pane">
    <div v-if="documentStore.currentFile" class="file-header">
      <el-icon><Document /></el-icon>
      <span class="file-path">{{ documentStore.currentFile.path }}</span>
    </div>
    <div v-else class="empty-state">
      <el-empty description="请选择一个文件" />
    </div>
    <div v-if="documentStore.isLoading" class="loading">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>加载中...</span>
    </div>
    <div v-else-if="documentStore.error" class="error">
      <el-icon><Warning /></el-icon>
      <span>{{ documentStore.error }}</span>
    </div>
    <div v-else-if="documentStore.currentFile" class="doc-view">
      <DocumentViewer />
    </div>
    <SelectionToolbar
      :visible="selectionVisible"
      :position="selectionPosition"
      :selected-text="selectedText"
      @chat="handleToolbarChat"
      @flashcard="handleToolbarFlashcard"
      @summary="handleToolbarSummary"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { Document, Loading, Warning } from '@element-plus/icons-vue'
import { useDocumentStore } from '@/stores/document'
import DocumentViewer from '@/components/DocumentViewer.vue'
import SelectionToolbar from '@/components/shared/SelectionToolbar.vue'

const documentStore = useDocumentStore()

const selectedText = ref('')
const selectionVisible = ref(false)
const selectionPosition = ref({ left: 0, top: 0 })

function handleSelection() {
  const selection = window.getSelection()
  const text = selection.toString().trim()

  if (text.length > 4) {
    selectedText.value = text
    selectionVisible.value = true

    const range = selection.getRangeAt(0)
    const rect = range.getBoundingClientRect()
    const containerRect = document.querySelector('.doc-view')?.getBoundingClientRect()

    if (containerRect) {
      selectionPosition.value = {
        left: rect.left - containerRect.left + 20,
        top: rect.top - containerRect.top - 10
      }
    }
  } else {
    selectionVisible.value = false
  }
}

function handleToolbarChat(text) {
  console.log('Chat about:', text)
  selectionVisible.value = false
}

function handleToolbarFlashcard(text) {
  console.log('Generate flashcard:', text)
  selectionVisible.value = false
}

function handleToolbarSummary(text) {
  console.log('Generate summary:', text)
  selectionVisible.value = false
}

onMounted(() => {
  document.addEventListener('mouseup', handleSelection)
})

onUnmounted(() => {
  document.removeEventListener('mouseup', handleSelection)
})
</script>

<style scoped>
.content-pane {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: var(--el-bg-color-page);
  position: relative;
}

.file-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  background-color: var(--el-bg-color);
}

.file-path {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.empty-state,
.loading,
.error {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--el-text-color-secondary);
}

.doc-view {
  flex: 1;
  overflow: hidden;
  position: relative;
}
</style>
