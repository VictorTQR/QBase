<template>
  <div class="main-layout">
    <header class="header">
      <div class="logo">QBase</div>
      <div class="actions">
        <el-button @click="handleAddFolder" type="primary">
          <el-icon><FolderAdd /></el-icon>
          添加文件夹
        </el-button>
      </div>
    </header>
    <div class="content">
      <slot />
    </div>
  </div>
</template>

<script setup>
import { FolderAdd } from '@element-plus/icons-vue'
import { useWorkspaceStore } from '@/stores/workspace'

const workspaceStore = useWorkspaceStore()

async function handleAddFolder() {
  const result = await window.electronAPI.selectFolder()
  if (result) {
    workspaceStore.addFolder(result)
  }
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

.content {
  flex: 1;
  display: flex;
  overflow: hidden;
}
</style>
