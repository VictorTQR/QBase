<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useParseStore } from '@/stores/parse'
import { useVectorStore } from '@/stores/vector'
import { useRouter } from 'vue-router'
import FileManagementView from '@/components/parse/FileManagementView.vue'
import KanbanView from '@/components/parse/KanbanView.vue'
import ParseStatsView from '@/components/parse/ParseStatsView.vue'

const router = useRouter()
const parseStore = useParseStore()
const vectorStore = useVectorStore()

const activeTab = ref('files')
const wsMineru = ref(null)
const wsAudio = ref(null)

function goBack() {
  router.push('/')
}

function refresh() {
  parseStore.fetchTasks()
  parseStore.fetchStats()
  vectorStore.loadStats()
  vectorStore.loadIndexedFiles()
}

function connectWebSocket() {
  try {
    wsMineru.value = new WebSocket('ws://localhost:8000/ws/tasks/mineru')
    wsMineru.value.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'task_update') {
        parseStore.fetchTasks()
        parseStore.fetchStats()
      }
    }
  } catch (e) {
    console.error('MinerU WebSocket连接失败:', e)
  }

  try {
    wsAudio.value = new WebSocket('ws://localhost:8000/ws/tasks/audio')
    wsAudio.value.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'task_update') {
        parseStore.fetchTasks()
        parseStore.fetchStats()
      }
    }
  } catch (e) {
    console.error('Audio WebSocket连接失败:', e)
  }
}

function disconnectWebSocket() {
  if (wsMineru.value) {
    wsMineru.value.close()
  }
  if (wsAudio.value) {
    wsAudio.value.close()
  }
}

onMounted(async () => {
  await Promise.all([
    parseStore.fetchTasks(),
    parseStore.fetchStats(),
    vectorStore.loadStats(),
    vectorStore.loadIndexedFiles()
  ])
  connectWebSocket()
})

onUnmounted(() => {
  disconnectWebSocket()
})
</script>

<template>
  <div class="parse-management">
    <header class="header">
      <div class="header-left">
        <button class="back-btn" @click="goBack">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 12H5M12 19l-7-7 7-7"/>
          </svg>
        </button>
        <h1 class="header-title">解析管理</h1>
      </div>
      <div class="header-right">
        <el-button @click="refresh">
          <template #icon>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.3"/>
            </svg>
          </template>
          刷新
        </el-button>
      </div>
    </header>

    <div class="tabs-container">
      <el-tabs v-model="activeTab" class="parse-tabs">
        <el-tab-pane label="文件管理" name="files" />
        <el-tab-pane label="看板视图" name="kanban" />
        <el-tab-pane label="解析统计" name="stats" />
      </el-tabs>
    </div>

    <div v-if="vectorStore.isIndexing" class="indexing-banner">
      <div class="indexing-content">
        <span class="indexing-text">
          正在索引: {{ vectorStore.currentIndexingFile }}
          ({{ vectorStore.indexingProgress }}/{{ vectorStore.indexingTotal }})
        </span>
        <el-progress
          :percentage="Math.round((vectorStore.indexingProgress / vectorStore.indexingTotal) * 100)"
          :stroke-width="8"
          style="width: 200px"
        />
      </div>
    </div>

    <div class="main-content">
      <FileManagementView v-if="activeTab === 'files'" />
      <KanbanView v-if="activeTab === 'kanban'" />
      <ParseStatsView v-if="activeTab === 'stats'" />
    </div>
  </div>
</template>

<style scoped>
.parse-management {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color-page);
}

.header {
  height: 56px;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-lighter);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--el-text-color-secondary);
  transition: all 0.2s;
}

.back-btn:hover {
  background: var(--el-fill-color-lighter);
  color: var(--el-text-color-primary);
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.tabs-container {
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-lighter);
  padding: 0 24px;
}

.parse-tabs {
  height: 100%;
}

.parse-tabs :deep(.el-tabs__content) {
  display: none;
}

.indexing-banner {
  background: #dbeafe;
  border-bottom: 1px solid #bfdbfe;
  padding: 12px 24px;
}

.indexing-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.indexing-text {
  font-size: 14px;
  font-weight: 500;
  color: #1e40af;
}

.main-content {
  flex: 1;
  overflow: hidden;
  padding: 20px 24px;
}
</style>
