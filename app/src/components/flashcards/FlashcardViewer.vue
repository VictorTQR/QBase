<template>
  <div class="flashcard-viewer">
    <div v-if="!flashcardStore.currentCard" class="empty">
      <el-empty description="请先生成或选择一个闪卡集" />
    </div>
    <div v-else class="viewer-content">
      <div class="progress">
        {{ flashcardStore.progress.current }} / {{ flashcardStore.progress.total }}
      </div>

      <div
        class="flashcard"
        :class="{ flipped: flashcardStore.isFlipped }"
        @click="flashcardStore.flipCard"
      >
        <div class="card-face front">
          <div class="difficulty" :class="flashcardStore.currentCard?.difficulty">
            {{ getDifficultyLabel(flashcardStore.currentCard?.difficulty) }}
          </div>
          <div class="content">
            {{ flashcardStore.currentCard?.front }}
          </div>
          <div class="hint">点击卡片查看答案</div>
        </div>
        <div class="card-face back">
          <div class="content">
            {{ flashcardStore.currentCard?.back }}
          </div>
          <div class="hint">点击卡片返回问题</div>
        </div>
      </div>

      <div class="actions">
        <el-button-group>
          <el-button
            :disabled="flashcardStore.progress.current <= 1"
            @click="flashcardStore.prevCard"
          >
            <el-icon><DArrowLeft /></el-icon>
            上一张
          </el-button>
          <el-button
            v-if="!flashcardStore.currentCard?.mastered"
            type="success"
            @click="markMastered"
          >
            <el-icon><CircleCheck /></el-icon>
            已掌握
          </el-button>
          <el-tag v-else type="success" style="margin: 0 8px">已掌握</el-tag>
          <el-button
            :disabled="flashcardStore.progress.current >= flashcardStore.progress.total"
            @click="flashcardStore.nextCard"
          >
            下一张
            <el-icon><DArrowRight /></el-icon>
          </el-button>
        </el-button-group>
      </div>
    </div>
  </div>
</template>

<script setup>
import { DArrowLeft, DArrowRight, CircleCheck } from '@element-plus/icons-vue'
import { useFlashcardStore } from '@/stores/flashcard'

const flashcardStore = useFlashcardStore()

function getDifficultyLabel(difficulty) {
  const labels = {
    easy: '简单',
    medium: '中等',
    hard: '困难',
  }
  return labels[difficulty] || '中等'
}

function markMastered() {
  if (flashcardStore.currentCard) {
    flashcardStore.markMastered(flashcardStore.currentCard.id)
  }
}
</script>

<style scoped>
.flashcard-viewer {
  padding: 16px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.viewer-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.progress {
  text-align: center;
  color: var(--el-text-color-secondary);
  font-size: 14px;
  margin-bottom: 16px;
}

.flashcard {
  flex: 1;
  perspective: 1000px;
  cursor: pointer;
  min-height: 300px;
}

.card-face {
  position: absolute;
  width: 100%;
  height: 100%;
  backface-visibility: hidden;
  border-radius: 12px;
  background-color: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  padding: 24px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  transition: transform 0.6s;
}

.front {
  transform: rotateY(0deg);
}

.back {
  transform: rotateY(180deg);
  background: linear-gradient(135deg, var(--el-color-primary-light-9), var(--el-bg-color));
}

.flipped .front {
  transform: rotateY(180deg);
}

.flipped .back {
  transform: rotateY(360deg);
}

.difficulty {
  align-self: flex-start;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  margin-bottom: 16px;
}

.difficulty.easy {
  background-color: var(--el-color-success-light-9);
  color: var(--el-color-success);
}

.difficulty.medium {
  background-color: var(--el-color-warning-light-9);
  color: var(--el-color-warning);
}

.difficulty.hard {
  background-color: var(--el-color-danger-light-9);
  color: var(--el-color-danger);
}

.content {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  font-size: 18px;
  line-height: 1.6;
  color: var(--el-text-color-primary);
}

.hint {
  text-align: center;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 16px;
}

.actions {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}
</style>
