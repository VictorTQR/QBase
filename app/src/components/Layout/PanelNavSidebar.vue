<script setup>
import { computed } from 'vue'
import { ChatDotRound, Tickets, MagicStick } from '@element-plus/icons-vue'

const props = defineProps({
  activeModule: {
    type: String,
    default: 'chat'
  }
})

const emit = defineEmits(['change'])

const navItems = [
  { id: 'chat', icon: ChatDotRound, label: '对话' },
  { id: 'flashcard', icon: Tickets, label: '闪卡' },
  { id: 'generate', icon: MagicStick, label: '生成' }
]

const isActive = computed(() => (id) => props.activeModule === id)

const handleClick = (item) => {
  emit('change', item.id)
}
</script>

<template>
  <div class="panel-nav-sidebar">
    <div
      v-for="item in navItems"
      :key="item.id"
      class="nav-item"
      :class="{ active: isActive(item.id) }"
      @click="handleClick(item)"
    >
      <el-icon :size="20">
        <component :is="item.icon" />
      </el-icon>
      <span class="nav-label">{{ item.label }}</span>
    </div>
  </div>
</template>

<style scoped>
.panel-nav-sidebar {
  width: 64px;
  height: 100%;
  background-color: var(--el-bg-color-page);
  border-left: 1px solid var(--el-border-color-lighter);
  padding: 16px 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.nav-item {
  width: 48px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
  color: var(--el-text-color-secondary);
}

.nav-item:hover {
  background-color: var(--el-bg-color-secondary);
  transform: scale(1.05);
}

.nav-item.active {
  background-color: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}

.nav-label {
  font-size: 11px;
  text-align: center;
  line-height: 1;
}
</style>
