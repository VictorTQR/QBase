<template>
  <el-dialog v-model="visible" title="LLM 配置" width="500px">
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
    <template #footer>
      <el-button @click="handleTest">测试连接</el-button>
      <el-button @click="handleCancel">取消</el-button>
      <el-button type="primary" @click="handleConfirm">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useAgentStore } from '@/stores/agent'

const props = defineProps(['modelValue'])
const emit = defineEmits(['update:modelValue'])

const agentStore = useAgentStore()

const visible = ref(false)
const form = ref({
  type: 'openai',
  baseUrl: '',
  apiKey: '',
  model: '',
})

watch(
  () => props.modelValue,
  (val) => {
    visible.value = val
    if (val) {
      form.value = { ...agentStore.llmConfig }
    }
  },
)

watch(visible, (val) => {
  emit('update:modelValue', val)
})

function handleTest() {
  console.log('测试连接功能待实现')
}

function handleCancel() {
  visible.value = false
}

function handleConfirm() {
  agentStore.setLlmConfig(form.value)
  visible.value = false
}
</script>
