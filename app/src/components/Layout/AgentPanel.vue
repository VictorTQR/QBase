<template>
  <div class="agent-panel">
    <div class="panel-header">
      <span>AI 助手</span>
    </div>
    <div class="panel-content">
      <el-empty description="v0.2 敬请期待">
        <template #image>
          <el-icon :size="80"><ChatDotRound /></el-icon>
        </template>
      </el-empty>
    </div>
  </div>
</template>

<script setup>
import { ChatDotRound } from '@element-plus/icons-vue'
</script>

<style scoped>
.agent-panel {
  width: 25%;
  min-width: 200px;
  border-left: 1px solid var(--el-border-color);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  padding: 12px 16px;
  font-weight: 600;
  font-size: 14px;
  color: var(--el-text-color-secondary);
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.panel-content {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
