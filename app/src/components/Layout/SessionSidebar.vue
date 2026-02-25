<template>
  <div class="session-sidebar">
    <div class="sidebar-header">
      <span>对话历史</span>
      <el-button size="small" circle @click="handleNewSession">
        <el-icon><Plus /></el-icon>
      </el-button>
    </div>
    <div class="session-list">
      <div
        v-for="session in agentStore.sessions"
        :key="session.id"
        :class="['session-item', { active: agentStore.currentSessionId === session.id }]"
        @click="handleSwitchSession(session.id)"
      >
        <div class="session-title">{{ session.title }}</div>
        <div class="session-date">{{ formatDate(session.updatedAt) }}</div>
        <el-button
          size="small"
          circle
          class="delete-btn"
          @click.stop="handleDeleteSession(session.id)"
        >
          <el-icon><Delete /></el-icon>
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Plus, Delete } from '@element-plus/icons-vue'
import { useAgentStore } from '@/stores/agent'

const agentStore = useAgentStore()

function formatDate(isoString) {
  const date = new Date(isoString)
  const now = new Date()
  const diff = now - date

  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  return date.toLocaleDateString('zh-CN')
}

function handleNewSession() {
  agentStore.createSession()
}

function handleSwitchSession(sessionId) {
  agentStore.switchSession(sessionId)
}

function handleDeleteSession(sessionId) {
  agentStore.deleteSession(sessionId)
}
</script>

<style scoped>
.session-sidebar {
  width: 200px;
  border-right: 1px solid var(--el-border-color);
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color-page);
}

.sidebar-header {
  padding: 12px 16px;
  font-weight: 600;
  font-size: 14px;
  color: var(--el-text-color-secondary);
  border-bottom: 1px solid var(--el-border-color-lighter);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.session-item {
  padding: 10px 12px;
  margin-bottom: 4px;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  transition: background 0.2s;
}

.session-item:hover {
  background: var(--el-fill-color-light);
}

.session-item.active {
  background: var(--el-color-primary-light-9);
}

.session-title {
  font-size: 13px;
  color: var(--el-text-color-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding-right: 24px;
}

.session-date {
  font-size: 11px;
  color: var(--el-text-color-tertiary);
  margin-top: 4px;
}

.delete-btn {
  position: absolute;
  right: 4px;
  top: 50%;
  transform: translateY(-50%);
  opacity: 0;
  transition: opacity 0.2s;
}

.session-item:hover .delete-btn {
  opacity: 1;
}
</style>
