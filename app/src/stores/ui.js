import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUiStore = defineStore(
  'ui',
  () => {
    const activeModule = ref('chat')
    const isAgentPanelVisible = ref(true)
    const isFlashcardFocusMode = ref(false)
    const layoutMode = ref('split')
    const theme = ref('light')

    function setActiveModule(moduleId) {
      activeModule.value = moduleId
    }

    function toggleAgentPanel() {
      isAgentPanelVisible.value = !isAgentPanelVisible.value
    }

    function toggleFlashcardFocusMode() {
      isFlashcardFocusMode.value = !isFlashcardFocusMode.value
    }

    function setLayoutMode(mode) {
      layoutMode.value = mode
    }

    function setTheme(themeVal) {
      theme.value = themeVal
      document.documentElement.setAttribute('data-theme', themeVal)
    }

    return {
      activeModule,
      isAgentPanelVisible,
      isFlashcardFocusMode,
      layoutMode,
      theme,
      setActiveModule,
      toggleAgentPanel,
      toggleFlashcardFocusMode,
      setLayoutMode,
      setTheme,
    }
  },
  {
    persist: {
      key: 'qbase-ui',
      paths: ['layoutMode', 'theme'],
    },
  },
)
