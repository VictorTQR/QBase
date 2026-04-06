<template>
  <div class="main-layout">
    <header class="header">
      <div class="logo">
        <div class="logo-mark">QB</div>
        <span>QBase</span>
      </div>
      <div class="workspace-display" @click="handleOpenWorkspaceSelector">
        <el-icon><Folder /></el-icon>
        <span class="workspace-name">{{ workspaceStore.workspaceName }}</span>
        <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
      </div>
      <div class="actions">
        <div class="mode-selector">
          <button
            v-for="mode in layoutModes"
            :key="mode"
            class="mode-btn"
            :class="{ active: uiStore.layoutMode === mode }"
            @click="uiStore.setLayoutMode(mode)"
            :title="modeLabels[mode]"
          >
            {{ modeIcons[mode] }}
          </button>
        </div>
        <el-button @click="handleOpenSearch" link>
          <el-icon><Search /></el-icon>
          <span class="search-hint">搜索 (Ctrl+K)</span>
        </el-button>
        <el-button @click="handleOpenSettings" link>
          <el-icon><Setting /></el-icon>
        </el-button>
      </div>
    </header>
    <div class="main-area" :data-mode="uiStore.layoutMode">
      <slot />
    </div>
    <SearchPanel />
    <CommandPalette v-model="showCommandPalette" @execute="handleCommandExecute" />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { Folder, Search, Setting, ArrowDown } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { useWorkspaceStore } from '@/stores/workspace'
import { useSearchStore } from '@/stores/search'
import { useUiStore } from '@/stores/ui'
import { workspaceManager } from '@/utils/workspaceManager'
import SearchPanel from '@/components/SearchPanel.vue'
import CommandPalette from '@/components/shared/CommandPalette.vue'

const router = useRouter()
const workspaceStore = useWorkspaceStore()
const searchStore = useSearchStore()
const uiStore = useUiStore()

const layoutModes = ['split', 'focus', 'ai']
const modeLabels = { split: '分栏模式', focus: '专注模式', ai: 'AI 模式' }
const modeIcons = { split: '🔄', focus: '📖', ai: '🤖' }

const showCommandPalette = ref(false)

function handleKeyDown(e) {
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault()
    showCommandPalette.value = true
  }
  if (e.key === 'Escape') {
    showCommandPalette.value = false
  }
}

function handleCommandExecute(query) {
  console.log('Execute command:', query)
}

function handleOpenWorkspaceSelector() {
  router.push('/workspace-selector')
}

function handleOpenSearch() {
  searchStore.openPanel()
}

function handleOpenSettings() {
  router.push('/settings')
}

onMounted(() => {
  document.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeyDown)
})
</script>

<style scoped>
.main-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--el-bg-color);
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  height: 48px;
  border-bottom: 1px solid var(--el-border-color);
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
  font-size: 16px;
  color: var(--text-primary);
}

.logo-mark {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, var(--primary-500), var(--primary-700));
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 700;
  font-size: 14px;
}

.workspace-display {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.workspace-display:hover {
  background-color: var(--el-fill-color-light);
}

.workspace-name {
  font-size: 14px;
  color: var(--el-text-color-primary);
}

.dropdown-icon {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mode-selector {
  display: inline-flex;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  padding: 3px;
  gap: 2px;
}

.mode-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 6px 10px;
  border: none;
  background: transparent;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 14px;
  transition: all var(--duration-base) var(--ease-out);
}

.mode-btn:hover {
  background: var(--bg-secondary);
}

.mode-btn.active {
  background: var(--bg-primary);
  box-shadow: var(--shadow-sm);
  color: var(--primary-600);
}

.search-hint {
  font-size: 14px;
}

@media (max-width: 768px) {
  .search-hint {
    display: none;
  }
}

.main-area {
  flex: 1;
  display: grid;
  grid-template-columns: 260px 1fr 42%;
  grid-template-rows: 1fr;
  height: calc(100vh - 48px);
  transition: all var(--duration-slow) var(--ease-in-out);
  overflow: hidden;
}

.main-area[data-mode='focus'] {
  grid-template-columns: 0 1fr 0;
}

.main-area[data-mode='ai'] {
  grid-template-columns: 0 30% 1fr;
}

.main-area > * {
  overflow: hidden;
  transition: all var(--duration-slow) var(--ease-in-out);
  opacity: 1;
}

.main-area[data-mode='focus'] > *:nth-child(1),
.main-area[data-mode='focus'] > *:nth-child(3),
.main-area[data-mode='ai'] > *:nth-child(1) {
  opacity: 0;
  width: 0 !important;
  pointer-events: none;
}
</style>
