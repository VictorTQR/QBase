<template>
  <div class="main-layout">
    <header class="header">
      <div class="logo">QBase</div>
      <div class="actions">
        <el-button @click="handleOpenSearch" link>
          <el-icon><Search /></el-icon>
          <span class="search-hint">搜索 (Ctrl+K)</span>
        </el-button>
        <el-button @click="handleAddFolder" type="primary">
          <el-icon><FolderAdd /></el-icon>
          添加文件夹
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
import { FolderAdd, Search } from '@element-plus/icons-vue'
import { useWorkspaceStore } from '@/stores/workspace'
import { useSearchStore } from '@/stores/search'
import SearchPanel from '@/components/SearchPanel.vue'

const workspaceStore = useWorkspaceStore()
const searchStore = useSearchStore()

async function handleAddFolder() {
  const result = await window.electronAPI.selectFolder()
  if (result) {
    workspaceStore.addFolder(result)
  }
}

function handleOpenSearch() {
  searchStore.openPanel()
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
