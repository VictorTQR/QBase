<template>
  <div class="vector-settings">
    <el-form :model="form" label-width="140px">
      <el-form-item label="API Key">
        <el-input
          v-model="form.apiKey"
          type="password"
          show-password
          placeholder="请输入 SiliconFlow API Key"
        />
      </el-form-item>
      <el-form-item label="Base URL">
        <el-input v-model="form.baseUrl" />
      </el-form-item>
      <el-form-item label="Embedding Model">
        <el-select v-model="form.embeddingModel" style="width: 100%">
          <el-option label="BAAI/bge-large-zh-v1.5" value="BAAI/bge-large-zh-v1.5" />
          <el-option label="BAAI/bge-m3" value="BAAI/bge-m3" />
        </el-select>
      </el-form-item>
      <el-form-item label="ASR Model">
        <el-select v-model="form.asrModel" style="width: 100%">
          <el-option label="FunAudioLLM/SenseVoiceSmall" value="FunAudioLLM/SenseVoiceSmall" />
          <el-option label="TeleAI/TeleSpeechASR" value="TeleAI/TeleSpeechASR" />
        </el-select>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useAgentStore } from '@/stores/agent'

const agentStore = useAgentStore()
const isUpdating = ref(false)

const form = ref({
  apiKey: '',
  baseUrl: '',
  embeddingModel: '',
  asrModel: '',
})

watch(
  () => agentStore.llmConfig.siliconflow,
  (config) => {
    if (isUpdating.value) return
    isUpdating.value = true
    form.value = { ...config }
    setTimeout(() => {
      isUpdating.value = false
    }, 0)
  },
  { immediate: true, deep: true },
)

watch(
  form,
  (newForm) => {
    if (isUpdating.value) return
    isUpdating.value = true
    agentStore.setLlmConfig({
      ...agentStore.llmConfig,
      siliconflow: { ...newForm },
    })
    setTimeout(() => {
      isUpdating.value = false
    }, 0)
  },
  { deep: true },
)
</script>

<style scoped>
.vector-settings {
  padding: 8px 0;
}
</style>
