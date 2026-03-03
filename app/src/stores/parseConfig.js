import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useParseConfigStore = defineStore(
  'parseConfig',
  () => {
    const audioConfig = ref({
      provider: 'siliconflow',
      asrModel: 'FunAudioLLM/SenseVoiceSmall',
    })

    const docParseConfig = ref({
      provider: 'mineru',
      enableFormula: true,
      enableTable: true,
      enableOcr: true,
      language: 'auto',
    })

    function setAudioConfig(config) {
      audioConfig.value = { ...audioConfig.value, ...config }
    }

    function setDocParseConfig(config) {
      docParseConfig.value = { ...docParseConfig.value, ...config }
    }

    return {
      audioConfig,
      docParseConfig,
      setAudioConfig,
      setDocParseConfig,
    }
  },
  {
    persist: {
      key: 'qbase-parse-config',
    },
  },
)
