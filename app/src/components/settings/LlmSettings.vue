<template>
  <div class="llm-settings">
    <el-form :model="form" label-width="120px">
      <el-form-item label="API 类型">
        <el-radio-group v-model="form.type">
          <el-radio value="openai">OpenAI 兼容</el-radio>
          <el-radio value="ollama">Ollama</el-radio>
        </el-radio-group>
      </el-form-item>
      <el-form-item label="Base URL">
        <el-input v-model="form.baseUrl" placeholder="https://api.openai.com/v1" />
      </el-form-item>
      <el-form-item label="API Key">
        <el-input v-model="form.apiKey" type="password" show-password placeholder="sk-..." />
      </el-form-item>
      <el-form-item label="Model">
        <el-input v-model="form.model" placeholder="gpt-3.5-turbo" />
      </el-form-item>
      <el-form-item>
        <el-button :loading="isTesting" @click="handleTest" type="primary">测试连接</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useAgentStore } from '@/stores/agent'
import { ElMessage } from 'element-plus'

const agentStore = useAgentStore()
const isTesting = ref(false)
const isUpdating = ref(false)

const form = ref({
  type: 'openai',
  baseUrl: '',
  apiKey: '',
  model: '',
})

watch(
  () => agentStore.llmConfig,
  (config) => {
    if (isUpdating.value) return
    isUpdating.value = true
    form.value.type = config.type
    form.value.baseUrl = config.baseUrl
    form.value.apiKey = config.apiKey
    form.value.model = config.model
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
      type: newForm.type,
      baseUrl: newForm.baseUrl,
      apiKey: newForm.apiKey,
      model: newForm.model,
    })
    setTimeout(() => {
      isUpdating.value = false
    }, 0)
  },
  { deep: true },
)

async function handleTest() {
  if (!form.value.baseUrl || !form.value.model) {
    ElMessage.warning('请填写 Base URL 和 Model')
    return
  }

  isTesting.value = true
  try {
    const result = await agentStore.testConnection()
    if (result.success) {
      ElMessage.success(result.message)
    } else {
      ElMessage.error(result.message)
    }
  } catch (err) {
    ElMessage.error(`测试失败：${err.message}`)
  } finally {
    isTesting.value = false
  }
}
</script>

<style scoped>
.llm-settings {
  padding: 8px 0;
}
</style>
