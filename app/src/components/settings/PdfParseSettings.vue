<template>
  <div class="pdf-parse-settings">
    <el-form label-width="140px">
      <el-divider content-position="left">MinerU 配置</el-divider>

      <el-alert
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 16px"
      >
        API Key 和 Base URL 等敏感配置需在后端
        <code>.env</code> 文件中设置
      </el-alert>

      <el-form-item label="服务提供商">
        <el-select v-model="docParseConfig.provider" style="width: 200px">
          <el-option label="MinerU" value="mineru" />
        </el-select>
      </el-form-item>

      <el-divider content-position="left">高级选项</el-divider>

      <el-form-item label="启用公式识别">
        <el-switch v-model="docParseConfig.enableFormula" />
      </el-form-item>

      <el-form-item label="启用表格识别">
        <el-switch v-model="docParseConfig.enableTable" />
      </el-form-item>

      <el-form-item label="启用 OCR">
        <el-switch v-model="docParseConfig.enableOcr" />
      </el-form-item>

      <el-form-item label="语言">
        <el-select v-model="docParseConfig.language" style="width: 200px">
          <el-option label="自动检测" value="auto" />
          <el-option label="中文" value="zh" />
          <el-option label="英文" value="en" />
        </el-select>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useParseConfigStore } from '@/stores/parseConfig'

const parseConfigStore = useParseConfigStore()
const isUpdating = ref(false)

const docParseConfig = ref({
  provider: 'mineru',
  enableFormula: true,
  enableTable: true,
  enableOcr: true,
  language: 'auto',
})

watch(
  () => parseConfigStore.docParseConfig,
  (config) => {
    if (isUpdating.value) return
    isUpdating.value = true
    docParseConfig.value = { ...config }
    setTimeout(() => {
      isUpdating.value = false
    }, 0)
  },
  { immediate: true, deep: true },
)

watch(
  docParseConfig,
  (newConfig) => {
    if (isUpdating.value) return
    isUpdating.value = true
    parseConfigStore.setDocParseConfig({ ...newConfig })
    setTimeout(() => {
      isUpdating.value = false
    }, 0)
  },
  { deep: true },
)
</script>

<style scoped>
.pdf-parse-settings {
  padding: 8px 0;
}
</style>
