<template>
  <div class="parse-manager">
    <ParseStats
      :stats="stats"
      :loading="isParsing"
      @parse-all="handleParseAll"
      @retry-failed="handleRetryFailed"
    />
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
          :loading="isParsing"
          @close="handleCloseDetails"
          @reparse="handleReparse"
          @delete="handleDelete"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useParseStore } from '@/stores/parse'
import ParseStats from './ParseStats.vue'
import ParseQueue from './ParseQueue.vue'
import ParseDocumentList from './ParseDocumentList.vue'
import ParseDetails from './ParseDetails.vue'

const parseStore = useParseStore()
const isParsing = ref(false)

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

async function handleParseAll() {
  const pending = Object.entries(parseIndex.value)
    .filter(([, data]) => data.status === 'pending')
    .map(([filePath, data]) => ({ filePath, fileType: data.type || data.fileType }))

  if (pending.length === 0) {
    ElMessage.info('没有待解析的文件')
    return
  }

  isParsing.value = true
  try {
    ElMessage.info(`开始解析 ${pending.length} 个文件...`)
    await parseStore.startParseBatch(pending)
    ElMessage.success('批量解析完成')
  } catch (error) {
    ElMessage.error(`批量解析失败: ${error.message}`)
  } finally {
    isParsing.value = false
  }
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

async function handleReparse() {
  if (selectedFile.value) {
    const data = parseIndex.value[selectedFile.value]
    if (!data) return

    try {
      isParsing.value = true
      await parseStore.startParse(selectedFile.value, data.type || data.fileType)
      ElMessage.success('重新解析完成')
    } catch (error) {
      ElMessage.error(`解析失败: ${error.message}`)
    } finally {
      isParsing.value = false
    }
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
