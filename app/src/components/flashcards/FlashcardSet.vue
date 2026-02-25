<template>
  <div class="flashcard-set">
    <div v-if="flashcardStore.flashcardSets.length === 0" class="empty">
      <el-empty description="暂无闪卡集" :image-size="60" />
    </div>
    <div v-else class="set-list">
      <div
        v-for="set in flashcardStore.flashcardSets"
        :key="set.id"
        class="set-item"
        :class="{ active: set.id === flashcardStore.currentSetId }"
        @click="selectSet(set.id)"
      >
        <div class="set-info">
          <div class="set-title">{{ set.title }}</div>
          <div class="set-meta">
            <span>{{ set.flashcards.length }} 张卡片</span>
            <span class="separator">·</span>
            <span>{{ formatDate(set.createdAt) }}</span>
          </div>
        </div>
        <el-button
          type="danger"
          size="small"
          circle
          @click.stop="deleteSet(set.id)"
        >
          <el-icon><Delete /></el-icon>
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Delete } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import { useFlashcardStore } from '@/stores/flashcard'

const flashcardStore = useFlashcardStore()

function selectSet(id) {
  flashcardStore.selectSet(id)
  flashcardStore.viewMode = 'view'
}

async function deleteSet(id) {
  try {
    await ElMessageBox.confirm('确定要删除这个闪卡集吗？', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await flashcardStore.deleteSet(id)
  } catch {
  }
}

function formatDate(dateStr) {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.flashcard-set {
  padding: 16px;
  height: 100%;
  overflow-y: auto;
}

.empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.set-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.set-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-radius: 8px;
  background-color: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  cursor: pointer;
  transition: all 0.2s;
}

.set-item:hover {
  border-color: var(--el-color-primary-light-5);
}

.set-item.active {
  border-color: var(--el-color-primary);
  background-color: var(--el-color-primary-light-9);
}

.set-info {
  flex: 1;
  min-width: 0;
}

.setTitle {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.set-meta {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.separator {
  margin: 0 6px;
}
</style>
