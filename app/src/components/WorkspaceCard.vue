<template>
  <div class="workspace-card" @click="handleClick">
    <div class="card-icon">📁</div>
    <div class="card-content">
      <div class="card-name">{{ workspace.name }}</div>
      <div class="card-path">{{ workspace.path }}</div>
    </div>
    <div class="card-actions" @click.stop>
      <el-button link type="danger" size="small" @click="handleRemove">
        <el-icon><Delete /></el-icon>
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { Delete } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'

const props = defineProps({
  workspace: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['select', 'remove'])

function handleClick() {
  emit('select', props.workspace)
}

async function handleRemove() {
  try {
    await ElMessageBox.confirm(
      `确定要移除工作区「${props.workspace.name}」吗？`,
      '移除工作区',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    emit('remove', props.workspace)
  } catch {
  }
}
</script>

<style scoped>
.workspace-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.workspace-card:hover {
  border-color: var(--el-color-primary);
  background-color: var(--el-fill-color-lighter);
}

.card-icon {
  font-size: 32px;
  flex-shrink: 0;
}

.card-content {
  flex: 1;
  min-width: 0;
}

.card-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
}

.card-path {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-actions {
  flex-shrink: 0;
}
</style>
