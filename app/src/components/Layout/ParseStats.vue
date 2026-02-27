<template>
  <div class="parse-stats">
    <div class="stats-grid">
      <div class="stat-item">
        <div class="stat-value">{{ stats.total }}</div>
        <div class="stat-label">总计</div>
      </div>
      <div class="stat-item completed">
        <div class="stat-value">{{ stats.completed }}</div>
        <div class="stat-label">已完成</div>
      </div>
      <div class="stat-item pending">
        <div class="stat-value">{{ stats.pending }}</div>
        <div class="stat-label">待解析</div>
      </div>
      <div class="stat-item parsing">
        <div class="stat-value">{{ stats.parsing }}</div>
        <div class="stat-label">解析中</div>
      </div>
      <div class="stat-item failed">
        <div class="stat-value">{{ stats.failed }}</div>
        <div class="stat-label">失败</div>
      </div>
    </div>
    <div class="actions">
      <el-button size="small" @click="$emit('parse-all')">批量解析</el-button>
      <el-button size="small" type="warning" @click="$emit('retry-failed')" :disabled="stats.failed === 0">
        重试失败
      </el-button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  stats: {
    type: Object,
    required: true
  }
})

defineEmits(['parse-all', 'retry-failed'])
</script>

<style scoped>
.parse-stats {
  padding: 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 8px;
  margin-bottom: 12px;
}

.stat-item {
  text-align: center;
  padding: 8px 4px;
  border-radius: 4px;
  background: var(--el-fill-color-lighter);
}

.stat-item.completed {
  background: rgba(103, 194, 58, 0.1);
}

.stat-item.pending {
  background: rgba(230, 162, 60, 0.1);
}

.stat-item.parsing {
  background: rgba(64, 158, 255, 0.1);
}

.stat-item.failed {
  background: rgba(245, 108, 108, 0.1);
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.stat-label {
  font-size: 11px;
  color: var(--el-text-color-secondary);
  margin-top: 2px;
}

.actions {
  display: flex;
  gap: 8px;
  justify-content: center;
}
</style>
