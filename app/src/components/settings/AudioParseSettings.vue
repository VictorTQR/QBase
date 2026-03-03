<template>
  <div class="audio-parse-settings">
    <el-form label-width="140px">
      <el-divider content-position="left">音频解析配置</el-divider>

      <el-alert type="info" :closable="false" show-icon style="margin-bottom: 16px">
        API Key 和 Base URL 等敏感配置需在后端
        <code>.env</code> 文件中设置
      </el-alert>

      <el-form-item label="服务提供商">
        <el-select v-model="audioConfig.provider" style="width: 200px">
          <el-option label="硅基流动" value="siliconflow" />
        </el-select>
      </el-form-item>

      <el-form-item label="ASR 模型">
        <el-input v-model="audioConfig.asrModel" />
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useParseConfigStore } from '@/stores/parseConfig'

const parseConfigStore = useParseConfigStore()
const isUpdating = ref(false)

const audioConfig = ref({
  provider: 'siliconflow',
  asrModel: 'FunAudioLLM/SenseVoiceSmall',
})

watch(
  () => parseConfigStore.audioConfig,
  (config) => {
    if (isUpdating.value) return
    isUpdating.value = true
    audioConfig.value = { ...config }
    setTimeout(() => {
      isUpdating.value = false
    }, 0)
  },
  { immediate: true, deep: true },
)

watch(
  audioConfig,
  (newConfig) => {
    if (isUpdating.value) return
    isUpdating.value = true
    parseConfigStore.setAudioConfig({ ...newConfig })
    setTimeout(() => {
      isUpdating.value = false
    }, 0)
  },
  { deep: true },
)
</script>

<style scoped>
.audio-parse-settings {
  padding: 8px 0;
}
</style>
