<script setup>
import { ref } from 'vue'
import { useAgentStore } from '@/stores/agent'
import { useDocumentStore } from '@/stores/document'

const agentStore = useAgentStore()
const documentStore = useDocumentStore()

const isGenerating = ref(false)
const error = ref(null)
const summaryResult = ref(null)

async function generateSummary() {
  if (!documentStore.currentFile || !documentStore.content) {
    error.value = '请先打开一个 Markdown 文档'
    return
  }

  isGenerating.value = true
  error.value = null
  summaryResult.value = null

  try {
    const result = await agentStore.generateSummary(documentStore.content)
    if (result.success) {
      summaryResult.value = result.summary
    } else {
      error.value = result.error
    }
  } catch (err) {
    error.value = err.message
  } finally {
    isGenerating.value = false
  }
}
</script>

<template>
  <div class="summary-generator">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>文档摘要生成</span>
        </div>
      </template>

      <div class="content">
        <el-button
          type="primary"
          :loading="isGenerating"
          @click="generateSummary"
          style="width: 100%"
        >
          {{ isGenerating ? '生成中...' : '生成摘要' }}
        </el-button>

        <el-alert v-if="error" type="error" :closable="false" style="margin-top: 16px">
          {{ error }}
        </el-alert>

        <div v-if="summaryResult" class="result-panel">
          <h3>文档摘要</h3>
          <div class="summary-content">
            {{ summaryResult }}
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.summary-generator {
  padding: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-panel {
  margin-top: 20px;
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  background-color: #f9f9f9;
}

.result-panel h3 {
  margin-top: 0;
  margin-bottom: 12px;
  font-size: 16px;
  color: var(--el-text-color-primary);
}

.summary-content {
  line-height: 1.6;
  color: var(--el-text-color-regular);
}
</style>
