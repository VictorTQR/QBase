<template>
  <div class="settings-page">
    <header class="settings-header">
      <el-button @click="handleBack" link>
        <el-icon><ArrowLeft /></el-icon>
      </el-button>
      <div class="header-title">QBase 设置</div>
      <div></div>
    </header>
    <div class="settings-content">
      <SettingsSidebar v-model="activeTab" />
      <div class="settings-panel">
        <component :is="currentComponent" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import SettingsSidebar from '@/components/Layout/SettingsSidebar.vue'
import LlmSettings from '@/components/settings/LlmSettings.vue'
import PdfParseSettings from '@/components/settings/PdfParseSettings.vue'
import AudioParseSettings from '@/components/settings/AudioParseSettings.vue'
import VectorSettings from '@/components/settings/VectorSettings.vue'

const router = useRouter()
const activeTab = ref('llm')

const componentMap = {
  llm: LlmSettings,
  'pdf-parse': PdfParseSettings,
  'audio-parse': AudioParseSettings,
  vector: VectorSettings,
}

const currentComponent = computed(() => componentMap[activeTab.value] || LlmSettings)

function handleBack() {
  router.push('/')
}
</script>

<style scoped>
.settings-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--el-bg-color);
}

.settings-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  height: 48px;
  border-bottom: 1px solid var(--el-border-color);
}

.header-title {
  font-size: 18px;
  font-weight: bold;
  color: var(--el-text-color-primary);
}

.settings-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.settings-panel {
  flex: 1;
  padding: 24px 32px;
  overflow-y: auto;
}
</style>
