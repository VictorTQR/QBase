<template>
  <div class="parse-stats-view">
    <div class="view-header">
      <h2>解析统计</h2>
    </div>

    <div class="stats-cards">
      <div class="stat-card total">
        <div class="stat-icon">
          <el-icon><Document /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.total }}</div>
          <div class="stat-label">总计文件</div>
        </div>
      </div>
      <div class="stat-card completed">
        <div class="stat-icon">
          <el-icon><CircleCheck /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.done }}</div>
          <div class="stat-label">已完成</div>
        </div>
      </div>
      <div class="stat-card pending">
        <div class="stat-icon">
          <el-icon><Clock /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.pending }}</div>
          <div class="stat-label">待解析</div>
        </div>
      </div>
      <div class="stat-card failed">
        <div class="stat-icon">
          <el-icon><CircleClose /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.failed }}</div>
          <div class="stat-label">失败</div>
        </div>
      </div>
    </div>

    <div class="stats-details">
      <el-card class="detail-card">
        <template #header>
          <div class="card-header">
            <span>快速操作</span>
          </div>
        </template>
        <div class="quick-actions">
          <el-button
            type="primary"
            :disabled="stats.pending === 0 || isBatchParsing"
            :loading="isBatchParsing"
            @click="handleBatchParse"
          >
            批量解析待处理文件
          </el-button>
          <el-button
            type="warning"
            :disabled="stats.failed === 0 || isRetrying"
            :loading="isRetrying"
            @click="handleRetryFailed"
          >
            重试失败文件
          </el-button>
        </div>
      </el-card>

      <el-card class="detail-card">
        <template #header>
          <div class="card-header">
            <span>解析状态分布</span>
          </div>
        </template>
        <div class="status-distribution">
          <div v-if="stats.total === 0" class="empty-distribution">
            暂无数据
          </div>
          <div v-else class="distribution-bar">
            <div
              v-for="item in distributionData"
              :key="item.status"
              class="distribution-segment"
              :class="item.status"
              :style="{ width: item.percentage + '%' }"
              :title="`${item.label}: ${item.count} (${item.percentage.toFixed(1)}%)`"
            />
          </div>
          <div class="distribution-legend">
            <div v-for="item in distributionData" :key="item.status" class="legend-item">
              <span class="legend-dot" :class="item.status"></span>
              <span class="legend-label">{{ item.label }}: {{ item.count }}</span>
            </div>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Document, CircleCheck, Clock, CircleClose } from '@element-plus/icons-vue'
import { useParseStore } from '@/stores/parse'
import { ElMessage } from 'element-plus'

const parseStore = useParseStore()
const isBatchParsing = ref(false)
const isRetrying = ref(false)

const stats = computed(() => parseStore.stats)

const distributionData = computed(() => {
  const total = stats.value.total || 0
  const items = [
    { status: 'done', label: '已完成', count: stats.value.done },
    { status: 'pending', label: '待解析', count: stats.value.pending },
    { status: 'running', label: '解析中', count: stats.value.running },
    { status: 'failed', label: '失败', count: stats.value.failed },
  ]
  return items.map(item => ({
    ...item,
    percentage: total > 0 ? (item.count / total) * 100 : 0,
  }))
})

const handleBatchParse = async () => {
  if (stats.value.pending === 0) {
    ElMessage.warning('没有待解析的文件')
    return
  }

  try {
    isBatchParsing.value = true
    const response = await parseStore.batchParsePending()
    ElMessage.success(response.message)
  } catch (err) {
    ElMessage.error(err.message || '批量解析失败')
  } finally {
    isBatchParsing.value = false
  }
}

const handleRetryFailed = async () => {
  if (stats.value.failed === 0) {
    ElMessage.warning('没有失败的文件')
    return
  }

  try {
    isRetrying.value = true
    const response = await parseStore.retryFailedTasks()
    ElMessage.success(response.message)
  } catch (err) {
    ElMessage.error(err.message || '重试失败')
  } finally {
    isRetrying.value = false
  }
}
</script>

<style scoped>
.parse-stats-view {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.view-header {
  margin-bottom: 20px;
}

.view-header h2 {
  margin: 0;
  font-size: 20px;
  color: var(--el-text-color-primary);
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: var(--el-bg-color-page);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.stat-card.total .stat-icon {
  background: rgba(144, 147, 153, 0.1);
  color: var(--el-text-color-secondary);
}

.stat-card.completed .stat-icon {
  background: rgba(103, 194, 58, 0.1);
  color: var(--el-color-success);
}

.stat-card.pending .stat-icon {
  background: rgba(230, 162, 60, 0.1);
  color: var(--el-color-warning);
}

.stat-card.failed .stat-icon {
  background: rgba(245, 108, 108, 0.1);
  color: var(--el-color-danger);
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}

.stats-details {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.detail-card {
  margin-bottom: 0;
}

.card-header {
  font-weight: 600;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.status-distribution {
  padding: 16px 0;
}

.empty-distribution {
  text-align: center;
  color: var(--el-text-color-placeholder);
  padding: 40px 0;
}

.distribution-bar {
  height: 32px;
  display: flex;
  border-radius: 6px;
  overflow: hidden;
  margin-bottom: 16px;
}

.distribution-segment {
  transition: width 0.3s;
}

.distribution-segment.done {
  background: var(--el-color-success);
}

.distribution-segment.pending {
  background: var(--el-color-warning);
}

.distribution-segment.running {
  background: var(--el-color-primary);
}

.distribution-segment.failed {
  background: var(--el-color-danger);
}

.distribution-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.legend-dot.done {
  background: var(--el-color-success);
}

.legend-dot.pending {
  background: var(--el-color-warning);
}

.legend-dot.running {
  background: var(--el-color-primary);
}

.legend-dot.failed {
  background: var(--el-color-danger);
}

.legend-label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
</style>
