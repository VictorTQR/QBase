<template>
  <div class="flashcard-generator">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>生成闪卡</span>
        </div>
      </template>

      <div class="content">
        <div class="form-item">
          <span class="label">闪卡数量</span>
          <el-slider v-model="flashcardCount" :min="5" :max="20" :step="1" show-input />
        </div>

        <el-button
          type="primary"
          :loading="flashcardStore.isGenerating"
          @click="generate"
          style="width: 100%; margin-top: 16px"
        >
          {{ flashcardStore.isGenerating ? '生成中...' : '生成闪卡' }}
        </el-button>

        <el-alert
          v-if="flashcardStore.generateError"
          type="error"
          :closable="false"
          style="margin-top: 16px"
        >
          {{ flashcardStore.generateError }}
        </el-alert>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useFlashcardStore } from '@/stores/flashcard'

const flashcardStore = useFlashcardStore()
const flashcardCount = ref(10)

async function generate() {
  await flashcardStore.generateFlashcards(flashcardCount.value)
}
</script>

<style scoped>
.flashcard-generator {
  padding: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-item {
  margin-bottom: 16px;
}

.label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  color: var(--el-text-color-regular);
}
</style>
