<template>
  <div class="main-layout">
    <header class="header">
      <div class="logo">QBase</div>
      <div class="workspace-display" @click="handleOpenWorkspaceSelector">
        <el-icon><Folder /></el-icon>
        <span class="workspace-name">{{ workspaceStore.workspaceName }}</span>
        <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
      </div>
      <div class="actions">
        <el-button @click="handleOpenSearch" link>
          <el-icon><Search /></el-icon>
          <span class="search-hint">搜索 (Ctrl+K)</span>
        </el-button>
        <el-button @click="handleOpenSettings" link>
          <el-icon><Setting /></el-icon>
        </el-button>
      </div>
    </header>
    <div class="content">
      <slot />
    </div>
    <SearchPanel />
  </div>
</template>

<script setup>
import { Folder, Search, Setting, ArrowDown } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { useWorkspaceStore } from '@/stores/workspace'
import { useSearchStore } from '@/stores/search'
import { workspaceManager } from '@/utils/workspaceManager'
import SearchPanel from '@/components/SearchPanel.vue'

const router = useRouter()
const workspaceStore = useWorkspaceStore()
const searchStore = useSearchStore()

function handleOpenWorkspaceSelector() {
  router.push('/workspace-selector')
}

function handleOpenSearch() {
  searchStore.openPanel()
}

function handleOpenSettings() {
  router.push('/settings')
}
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
  font-size: 18px;
  font-weight: bold;
  color: var(--el-text-color-primary);
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

.search-hint {
  font-size: 14px;
}

@media (max-width: 768px) {
  .search-hint {
    display: none;
  }
}

.content {
  flex: 1;
  display: flex;
  overflow: hidden;
}
</style>
