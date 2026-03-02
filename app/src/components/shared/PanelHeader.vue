<script setup>
import { Minus } from '@element-plus/icons-vue'

defineProps({
  title: {
    type: String,
    default: 'AI 助手',
  },
})

const emit = defineEmits(['minimize'])
</script>

<template>
  <div class="panel-header">
    <span class="panel-title">{{ title }}</span>
    <div class="header-actions">
      <el-button size="small" circle @click="$emit('minimize')">
        <el-icon><Minus /></el-icon>
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.panel-header {
  height: 48px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.panel-title {
  font-weight: 600;
  font-size: 14px;
}

.header-actions {
  display: flex;
  gap: 8px;
}
</style>
