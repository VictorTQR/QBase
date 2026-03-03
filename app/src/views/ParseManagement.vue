<template>
  <div class="parse-management-page">
    <header class="page-header">
      <el-button @click="handleBack" link>
        <el-icon><ArrowLeft /></el-icon>
      </el-button>
      <div class="header-title">解析管理</div>
      <div class="header-actions">
        <el-button size="small" :loading="parseStore.isLoading" @click="handleRefresh">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </header>

    <div v-if="parseStore.error" class="error-banner">
      <el-alert type="error" :closable="true" @close="parseStore.clearError">
        {{ parseStore.error }}
      </el-alert>
    </div>

    <div v-if="vectorStore.isIndexing" class="indexing-progress-banner">
      <el-alert type="info" :closable="false">
        <div class="indexing-content">
          <span class="indexing-text">
            正在索引: {{ vectorStore.currentIndexingFile }} ({{ vectorStore.indexingProgress }}/{{
              vectorStore.indexingTotal
            }})
          </span>
          <el-progress
            :percentage="indexingPercentage"
            :stroke-width="8"
            style="width: 200px; margin-left: 16px"
          />
        </div>
      </el-alert>
    </div>

    <div class="page-content">
      <ParseSidebar v-model="activeTab" />
      <div class="content-panel">
        <component :is="currentComponent" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, Refresh } from '@element-plus/icons-vue'
import { useParseStore } from '@/stores/parse'
import { useVectorStore } from '@/stores/vector'
import ParseSidebar from '@/components/Layout/ParseSidebar.vue'
import ParseQueueView from '@/components/parse/ParseQueueView.vue'
import ParseDocumentsView from '@/components/parse/ParseDocumentsView.vue'
import ParseStatsView from '@/components/parse/ParseStatsView.vue'
import AudioParseView from '@/components/parse/AudioParseView.vue'

const router = useRouter()
const parseStore = useParseStore()
const vectorStore = useVectorStore()
const activeTab = ref('queue')

const componentMap = {
  queue: ParseQueueView,
  documents: ParseDocumentsView,
  audio: AudioParseView,
  stats: ParseStatsView,
}

const currentComponent = computed(() => componentMap[activeTab.value] || ParseQueueView)

const indexingPercentage = computed(() => {
  if (vectorStore.indexingTotal === 0) return 0
  return Math.round((vectorStore.indexingProgress / vectorStore.indexingTotal) * 100)
})

onMounted(async () => {
  await parseStore.fetchTasks()
  await parseStore.fetchStats()
  try {
    await vectorStore.loadStats()
  } catch (err) {
    console.error('加载向量统计失败:', err)
  }
})

function handleBack() {
  router.push('/')
}

async function handleRefresh() {
  await parseStore.fetchTasks()
  await parseStore.fetchStats()
  try {
    await vectorStore.loadStats()
  } catch (err) {
    console.error('加载向量统计失败:', err)
  }
}
</script>

<style scoped>
.parse-management-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--el-bg-color);
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  height: 48px;
  border-bottom: 1px solid var(--el-border-color);
}

.header-title {
  font-size: 18px;
  font-weight: bold;
  color: var(--el-text-color-primary);
}

.header-actions {
  display: flex;
  gap: 8px;
}

.error-banner {
  padding: 8px 16px;
}

.indexing-progress-banner {
  padding: 8px 16px;
}

.indexing-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.indexing-text {
  font-size: 14px;
  color: var(--el-text-color-primary);
}

.page-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.content-panel {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  background: var(--el-bg-color);
}
</style>
