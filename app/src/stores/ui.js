import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUiStore = defineStore('ui', () => {
  const activeModule = ref('chat')
  const isAgentPanelVisible = ref(true)
  const isFlashcardFocusMode = ref(false)

  function setActiveModule(moduleId) {
    activeModule.value = moduleId
  }

  function toggleAgentPanel() {
    isAgentPanelVisible.value = !isAgentPanelVisible.value
  }

  function toggleFlashcardFocusMode() {
    isFlashcardFocusMode.value = !isFlashcardFocusMode.value
  }

  return {
    activeModule,
    isAgentPanelVisible,
    isFlashcardFocusMode,
    setActiveModule,
    toggleAgentPanel,
    toggleFlashcardFocusMode,
  }
})
