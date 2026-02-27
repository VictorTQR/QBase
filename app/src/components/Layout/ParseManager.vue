<template>
  <div class="parse-manager">
    <ParseStats :stats="stats" @parse-all="handleParseAll" @retry-failed="handleRetryFailed" />
    <div class="manager-content">
      <ParseQueue
        :pending-files="pendingFiles"
        :parsing-files="parsingFiles"
        :failed-files="failedFiles"
      />
      <div class="right-panel">
        <ParseDocumentList
          :parse-index="parseIndex"
          :selected-file="selectedFile"
          @select="handleSelectFile"
        />
        <ParseDetails
          :file-path="selectedFile"
          :file-data="selectedFileData"
          @close="handleCloseDetails"
          @reparse="handleReparse"
          @delete="handleDelete"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useParseStore } from '@/stores/parse'
import ParseStats from './ParseStats.vue'
import ParseQueue from './ParseQueue.vue'
import ParseDocumentList from './ParseDocumentList.vue'
import ParseDetails from './ParseDetails.vue'

const parseStore = useParseStore()

const parseIndex = computed(() => parseStore.parseIndex)
const stats = computed(() => parseStore.stats)
const pendingFiles = computed(() => parseStore.pendingFiles)
const parsingFiles = computed(() => parseStore.parsingFiles)
const failedFiles = computed(() => parseStore.failedFiles)
const selectedFile = computed(() => parseStore.selectedFile)

const selectedFileData = computed(() => {
  if (!selectedFile.value) return null
  return parseIndex.value[selectedFile.value] || null
})

function handleParseAll() {
  console.log('批量解析功能待实现')
}

function handleRetryFailed() {
  parseStore.retryFailed()
}

function handleSelectFile(filePath) {
  parseStore.selectFile(filePath)
}

function handleCloseDetails() {
  parseStore.closeDetails()
}

function handleReparse() {
  if (selectedFile.value) {
    parseStore.reparse(selectedFile.value)
  }
}

function handleDelete() {
  if (selectedFile.value) {
    parseStore.removeFile(selectedFile.value)
    parseStore.closeDetails()
  }
}
</script>

<style scoped>
.parse-manager {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.manager-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.right-panel {
  flex: 2;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-left: 1px solid var(--el-border-color-lighter);
}
</style>
