<template>
  <div class="parse-sidebar">
    <div
      v-for="item in navItems"
      :key="item.key"
      class="nav-item"
      :class="{ active: modelValue === item.key }"
      @click="$emit('update:modelValue', item.key)"
    >
      <el-icon><component :is="item.icon" /></el-icon>
      <span class="nav-label">{{ item.label }}</span>
    </div>
  </div>
</template>

<script setup>
import { Document, List, TrendCharts, Microphone } from '@element-plus/icons-vue'

defineProps({
  modelValue: {
    type: String,
    default: 'queue',
  },
})

defineEmits(['update:modelValue'])

const navItems = [
  { key: 'queue', label: '队列管理', icon: Document },
  { key: 'documents', label: '已解析文档', icon: List },
  { key: 'audio', label: '音频解析', icon: Microphone },
  { key: 'stats', label: '解析统计', icon: TrendCharts },
]
</script>

<style scoped>
.parse-sidebar {
  width: 200px;
  border-right: 1px solid var(--el-border-color);
  padding: 16px 0;
  background: var(--el-bg-color-page);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  cursor: pointer;
  transition: all 0.2s;
  color: var(--el-text-color-regular);
}

.nav-item:hover {
  background: var(--el-fill-color-light);
}

.nav-item.active {
  background: var(--el-fill-color);
  color: var(--el-color-primary);
  font-weight: 500;
  border-right: 3px solid var(--el-color-primary);
}

.nav-label {
  font-size: 14px;
}
</style>
