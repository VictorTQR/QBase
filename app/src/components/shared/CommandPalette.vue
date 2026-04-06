<template>
  <div
    class="command-overlay"
    :class="{ show: visible }"
    @click.self="close"
  >
    <div class="command-box">
      <div class="command-input-wrapper">
        <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"></circle>
          <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
        </svg>
        <input
          ref="inputRef"
          v-model="query"
          class="command-input"
          placeholder="⌘K 全局命令或搜索..."
          @keyup.esc="close"
          @keyup.enter="execute"
        >
      </div>
      <div class="command-filters">
        <span class="command-chip">📄 全文</span>
        <span class="command-chip">🤖 AI 生成</span>
        <span class="command-chip">🔄 重建索引</span>
        <span class="command-chip">🎨 切换深色</span>
      </div>
      <div class="command-footer">
        <span class="shortcut">
          <span class="kbd">↵</span> 确认执行
        </span>
        <span class="shortcut">
          <span class="kbd">ESC</span> 关闭
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'execute'])

const visible = ref(props.modelValue)
const query = ref('')
const inputRef = ref(null)

watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val) {
    nextTick(() => inputRef.value?.focus())
  } else {
    query.value = ''
  }
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

function close() {
  visible.value = false
}

function execute() {
  emit('execute', query.value)
  close()
}

defineExpose({
  focus: () => inputRef.value?.focus()
})
</script>

<style scoped>
.command-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15,23,42,0.45);
  backdrop-filter: blur(6px);
  z-index: 100;
  display: flex;
  justify-content: center;
  padding-top: 16vh;
  opacity: 0;
  pointer-events: none;
  transition: all var(--duration-base) var(--ease-out);
}

.command-overlay.show {
  opacity: 1;
  pointer-events: auto;
}

.command-box {
  width: 92%;
  max-width: 640px;
  background: var(--bg-primary);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-xl);
  overflow: hidden;
  transform: scale(0.96) translateY(10px);
  transition: all 0.25s cubic-bezier(0.34,1.56,0.64,1);
}

.command-overlay.show .command-box {
  transform: scale(1) translateY(0);
}

.command-input-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-subtle);
}

.search-icon {
  width: 20px;
  height: 20px;
  color: var(--text-muted);
  flex-shrink: 0;
}

.command-input {
  width: 100%;
  padding: 0;
  border: none;
  outline: none;
  font-size: 16px;
  background: transparent;
  font-family: var(--font-body);
  color: var(--text-primary);
}

.command-input::placeholder {
  color: var(--text-muted);
}

.command-filters {
  padding: 12px 16px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.command-chip {
  padding: 5px 10px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  font-size: 12px;
  cursor: pointer;
  border: 1px solid var(--border-subtle);
  transition: all var(--duration-fast) var(--ease-out);
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 6px;
}

.command-chip:hover {
  border-color: var(--primary-300);
  color: var(--primary-600);
  background: var(--primary-50);
}

.command-footer {
  padding: 12px 16px;
  background: var(--bg-secondary);
  font-size: 11px;
  color: var(--text-muted);
  display: flex;
  justify-content: space-between;
  border-top: 1px solid var(--border-subtle);
}

.shortcut {
  display: flex;
  align-items: center;
  gap: 8px;
}

.kbd {
  padding: 3px 6px;
  background: var(--bg-primary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
}
</style>
