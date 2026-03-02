<template>
  <div class="parse-management-page">
    <header class="page-header">
      <el-button @click="handleBack" link>
        <el-icon><ArrowLeft /></el-icon>
      </el-button>
      <div class="header-title">解析管理</div>
      <div class="header-actions">
        <el-button size="small" :loading="isParsing" @click="handleParseAll">
          开始全部解析
        </el-button>
        <el-button size="small" @click="handleExportAll" :disabled="stats.completed === 0">
          导出全部
        </el-button>
      </div>
    </header>
    <div class="page-content">
      <ParseSidebar v-model="activeTab" />
      <div class="content-panel">
        <component :is="currentComponent" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Download } from '@element-plus/icons-vue'
import { useParseStore } from '@/stores/parse'
import ParseSidebar from '@/components/Layout/ParseSidebar.vue'
import ParseQueueView from '@/components/parse/ParseQueueView.vue'
import ParseDocumentsView from '@/components/parse/ParseDocumentsView.vue'
import ParseStatsView from '@/components/parse/ParseStatsView.vue'

const router = useRouter()
const parseStore = useParseStore()
const activeTab = ref('queue')
const isParsing = ref(false)

const stats = computed(() => parseStore.stats)

const componentMap = {
  queue: ParseQueueView,
  documents: ParseDocumentsView,
  stats: ParseStatsView,
}

const currentComponent = computed(() => componentMap[activeTab.value] || ParseQueueView)

function handleBack() {
  router.push('/')
}

async function handleParseAll() {
  const pending = Object.entries(parseStore.parseIndex)
    .filter(([, data]) => data.status === 'pending')
    .map(([filePath, data]) => ({ filePath, fileType: data.fileType || data.type }))

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

function handleExportAll() {
  ElMessage.info('导出功能开发中')
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
