<template>
  <el-dialog v-model="visible" title="LLM 配置" width="600px">
    <el-tabs v-model="activeTab">
      <el-tab-pane label="LLM" name="llm">
        <el-form :model="form" label-width="100px">
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
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="MinerU (PDF)" name="mineru">
        <el-form :model="form.mineru" label-width="120px">
          <el-form-item label="API Key">
            <el-input
              v-model="form.mineru.apiKey"
              type="password"
              show-password
              placeholder="请输入 MinerU API Key"
            />
          </el-form-item>
          <el-form-item label="Base URL">
            <el-input v-model="form.mineru.baseUrl" />
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="SiliconFlow" name="siliconflow">
        <el-form :model="form.siliconflow" label-width="140px">
          <el-form-item label="API Key">
            <el-input
              v-model="form.siliconflow.apiKey"
              type="password"
              show-password
              placeholder="请输入 SiliconFlow API Key"
            />
          </el-form-item>
          <el-form-item label="Embedding Model">
            <el-select v-model="form.siliconflow.embeddingModel" style="width: 100%">
              <el-option label="BAAI/bge-large-zh-v1.5" value="BAAI/bge-large-zh-v1.5" />
              <el-option label="BAAI/bge-m3" value="BAAI/bge-m3" />
            </el-select>
          </el-form-item>
          <el-form-item label="ASR Model">
            <el-select v-model="form.siliconflow.asrModel" style="width: 100%">
              <el-option label="FunAudioLLM/SenseVoiceSmall" value="FunAudioLLM/SenseVoiceSmall" />
              <el-option label="TeleAI/TeleSpeechASR" value="TeleAI/TeleSpeechASR" />
            </el-select>
          </el-form-item>
        </el-form>
      </el-tab-pane>
    </el-tabs>

    <template #footer>
      <el-button :loading="isTesting" @click="handleTest">测试连接</el-button>
      <el-button @click="handleCancel">取消</el-button>
      <el-button type="primary" @click="handleConfirm">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useAgentStore } from '@/stores/agent'
import { ElMessage } from 'element-plus'

const props = defineProps(['modelValue'])
const emit = defineEmits(['update:modelValue'])

const agentStore = useAgentStore()

const visible = ref(false)
const activeTab = ref('llm')
const form = ref({
  type: 'openai',
  baseUrl: '',
  apiKey: '',
  model: '',
  mineru: {
    apiKey: '',
    baseUrl: 'https://mineru.net'
  },
  siliconflow: {
    apiKey: '',
    baseUrl: 'https://api.siliconflow.cn',
    embeddingModel: 'BAAI/bge-large-zh-v1.5',
    asrModel: 'FunAudioLLM/SenseVoiceSmall'
  }
})

const isTesting = ref(false)

watch(
  () => props.modelValue,
  (val) => {
    visible.value = val
    if (val) {
      form.value = deepMerge(form.value, agentStore.llmConfig)
    }
  },
)

watch(visible, (val) => {
  emit('update:modelValue', val)
})

function deepMerge(target, source) {
  const result = { ...target }
  for (const key in source) {
    if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
      result[key] = deepMerge(result[key] || {}, source[key])
    } else {
      result[key] = source[key]
    }
  }
  return result
}

async function handleTest() {
  if (activeTab.value === 'llm') {
    if (!form.value.baseUrl || !form.value.model) {
      ElMessage.warning('请填写 Base URL 和 Model')
      return
    }

    isTesting.value = true
    try {
      const originalConfig = { ...agentStore.llmConfig }
      agentStore.setLlmConfig(form.value)

      const result = await agentStore.testConnection()
      agentStore.setLlmConfig(originalConfig)

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
  } else {
    ElMessage.info('该 Tab 的测试功能待实现')
  }
}

function handleCancel() {
  visible.value = false
}

function handleConfirm() {
  agentStore.setLlmConfig(form.value)
  visible.value = false
}
</script>
