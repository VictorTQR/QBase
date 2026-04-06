<template>
  <div class="ws-page">
    <div class="ws-header">
      <h1>QBase</h1>
      <p>本地知识库 · AI 深度协作</p>
    </div>
    <div class="ws-grid">
      <div
        v-for="ws in workspaces"
        :key="ws.path"
        class="ws-card"
        @click="handleSelectWorkspace(ws)"
      >
        <h3>
          <span>📁</span>
          {{ ws.name }}
        </h3>
        <div class="ws-path">{{ ws.path }}</div>
        <div class="ws-meta">
          <span>📄 {{ ws.files || 0 }} 文件</span>
          <span>🕐 最近</span>
        </div>
      </div>
      <div class="ws-card create" @click="handleCreateWorkspace">
        <div class="ws-icon">➕</div>
        <h3>创建新工作区</h3>
      </div>
    </div>
    <div class="ws-actions">
      <button class="ws-btn" @click="showDemo">📖 快速入门</button>
      <button class="ws-btn primary" @click="handleOpenWorkspace">📂 打开已有</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { workspaceManager } from '@/utils/workspaceManager'

const router = useRouter()
const workspaces = ref([])

const workspacesWithNames = computed(() => {
  return workspaces.value.map(ws => ({
    ...ws,
    name: ws.path.split(/[/\\]/).pop()
  }))
})

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

function showDemo() {
  ElMessage.info('快速入门功能即将推出')
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
.ws-page {
  position: fixed;
  inset: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: white;
}

.ws-header {
  text-align: center;
  margin-bottom: 32px;
}

.ws-header h1 {
  margin: 0;
  font-size: 36px;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.ws-header p {
  margin-top: 8px;
  opacity: 0.9;
  font-size: 16px;
}

.ws-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
  width: 90%;
  max-width: 900px;
}

.ws-card {
  background: rgba(255,255,255,0.95);
  color: var(--text-primary);
  padding: 24px;
  border-radius: var(--radius-xl);
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-out);
  box-shadow: var(--shadow-lg);
}

.ws-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 40px rgba(0,0,0,0.2);
}

.ws-card h3 {
  margin: 0 0 6px;
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.ws-card .ws-path {
  font-size: 13px;
  color: var(--text-muted);
  font-family: var(--font-mono);
}

.ws-card .ws-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 12px;
}

.ws-card.create {
  background: rgba(255,255,255,0.75);
  border: 2px dashed rgba(255,255,255,0.5);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.ws-card.create .ws-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.ws-card.create h3 {
  color: var(--text-secondary);
  justify-content: center;
}

.ws-actions {
  display: flex;
  gap: 16px;
  margin-top: 32px;
}

.ws-btn {
  padding: 12px 24px;
  border-radius: var(--radius-lg);
  background: rgba(255,255,255,0.2);
  border: 1px solid rgba(255,255,255,0.4);
  color: white;
  cursor: pointer;
  font-weight: 500;
  font-size: 14px;
  transition: all var(--duration-base) var(--ease-out);
  display: flex;
  align-items: center;
  gap: 8px;
}

.ws-btn:hover {
  background: rgba(255,255,255,0.35);
  transform: translateY(-1px);
}

.ws-btn.primary {
  background: white;
  color: #764ba2;
  border-color: transparent;
}

.ws-btn.primary:hover {
  background: rgba(255,255,255,0.95);
}
</style>
