<template>
  <div class="settings-sidebar">
    <div
      v-for="item in menuItems"
      :key="item.key"
      class="menu-item"
      :class="{ active: activeKey === item.key }"
      @click="handleSelect(item.key)"
    >
      <el-icon><component :is="item.icon" /></el-icon>
      <span>{{ item.label }}</span>
    </div>
  </div>
</template>

<script setup>
import { ChatDotRound, Files, Connection } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: 'llm',
  },
})

const emit = defineEmits(['update:modelValue'])

const menuItems = [
  { key: 'llm', label: 'LLM', icon: ChatDotRound },
  { key: 'pdf-parse', label: 'PDF 解析', icon: Files },
  { key: 'vector', label: '向量存储', icon: Connection },
]

const activeKey = props.modelValue

function handleSelect(key) {
  emit('update:modelValue', key)
}
</script>

<style scoped>
.settings-sidebar {
  width: 200px;
  height: 100%;
  border-right: 1px solid var(--el-border-color);
  padding: 16px 0;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  cursor: pointer;
  color: var(--el-text-color-regular);
  transition: all 0.2s;
}

.menu-item:hover {
  background-color: var(--el-fill-color-light);
}

.menu-item.active {
  background-color: var(--el-fill-color-primary);
  color: var(--el-color-primary);
}

.menu-item .el-icon {
  font-size: 18px;
}
</style>
