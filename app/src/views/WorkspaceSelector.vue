<template>
  <div class="workspace-selector">
    <div class="selector-header">
      <h1>QBase</h1>
      <p class="subtitle">选择或创建工作区</p>
    </div>

    <div class="selector-content">
      <div v-if="workspaces.length > 0" class="workspace-list">
        <div class="section-title">
          <span>最近打开</span>
        </div>
        <div class="workspace-grid">
          <WorkspaceCard
            v-for="workspace in workspaces"
            :key="workspace.path"
            :workspace="workspace"
            @select="handleSelectWorkspace"
            @remove="handleRemoveWorkspace"
          />
        </div>
      </div>

      <div class="actions">
        <el-button type="primary" size="large" @click="handleOpenWorkspace">
          <el-icon><FolderOpened /></el-icon>
          打开文件夹作为工作区
        </el-button>
        <el-button size="large" @click="handleCreateWorkspace">
          <el-icon><FolderAdd /></el-icon>
          创建新工作区
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { FolderOpened, FolderAdd } from '@element-plus/icons-vue'
import { workspaceManager } from '@/utils/workspaceManager'
import WorkspaceCard from '@/components/WorkspaceCard.vue'

const router = useRouter()
const workspaces = ref([])

function loadWorkspaces() {
  workspaces.value = workspaceManager.getAllWorkspaces()
}

async function handleOpenWorkspace() {
  try {
    const result = await window.electronAPI.selectFolder()
    if (result) {
      openWorkspace(result.path)
    }
  } catch (error) {
    console.error('打开工作区失败:', error)
  }
}

async function handleCreateWorkspace() {
  try {
    const result = await window.electronAPI.selectFolder()
    if (result) {
      openWorkspace(result.path)
    }
  } catch (error) {
    console.error('创建工作区失败:', error)
  }
}

function handleSelectWorkspace(workspace) {
  openWorkspace(workspace.path)
}

function handleRemoveWorkspace(workspace) {
  workspaceManager.removeWorkspace(workspace.path)
  loadWorkspaces()
  ElMessage.success('工作区已移除')
}

function openWorkspace(workspacePath) {
  workspaceManager.addWorkspace(workspacePath)
  
  ElMessage.success('工作区已打开')
  router.push('/')
}

onMounted(() => {
  loadWorkspaces()
  
  const lastWorkspace = workspaceManager.getLastWorkspace()
  if (lastWorkspace) {
    openWorkspace(lastWorkspace)
  }
})
</script>

<style scoped>
.workspace-selector {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.selector-header {
  text-align: center;
  margin-bottom: 48px;
  color: white;
}

.selector-header h1 {
  font-size: 48px;
  font-weight: 700;
  margin-bottom: 8px;
}

.subtitle {
  font-size: 18px;
  opacity: 0.9;
}

.selector-content {
  width: 100%;
  max-width: 800px;
  background: white;
  border-radius: 16px;
  padding: 32px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 16px;
}

.workspace-list {
  margin-bottom: 32px;
}

.workspace-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.actions {
  display: flex;
  gap: 16px;
  justify-content: center;
}
</style>
