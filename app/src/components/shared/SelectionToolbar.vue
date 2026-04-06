<template>
  <div class="selection-toolbar" :class="{ show: visible }" :style="positionStyle">
    <button class="toolbar-btn primary" @click="handleChat">💬 提问</button>
    <button class="toolbar-btn" @click="handleFlashcard">🃏 闪卡</button>
    <button class="toolbar-btn" @click="handleSummary">📑 摘要</button>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  position: {
    type: Object,
    default: () => ({ left: 0, top: 0 }),
  },
  selectedText: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['chat', 'flashcard', 'summary'])

const positionStyle = computed(() => ({
  left: `${props.position.left}px`,
  top: `${props.position.top}px`,
}))

function handleChat() {
  emit('chat', props.selectedText)
}

function handleFlashcard() {
  emit('flashcard', props.selectedText)
}

function handleSummary() {
  emit('summary', props.selectedText)
}
</script>

<style scoped>
.selection-toolbar {
  position: absolute;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  padding: 6px;
  display: flex;
  gap: 4px;
  z-index: 30;
  transform: translateY(-10px);
  opacity: 0;
  pointer-events: none;
  transition: all var(--duration-base) var(--ease-out);
  border: 1px solid var(--border-medium);
}

.selection-toolbar.show {
  opacity: 1;
  pointer-events: auto;
  transform: translateY(0);
}

.toolbar-btn {
  padding: 8px 12px;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 13px;
  background: transparent;
  border: 1px solid transparent;
  transition: all var(--duration-fast) var(--ease-out);
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--text-secondary);
}

.toolbar-btn:hover {
  background: var(--bg-tertiary);
  border-color: var(--border-subtle);
  color: var(--text-primary);
}

.toolbar-btn.primary {
  background: var(--primary-50);
  color: var(--primary-700);
  border-color: var(--primary-200);
}

.toolbar-btn.primary:hover {
  background: var(--primary-100);
}
</style>
