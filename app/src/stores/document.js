import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useDocumentStore = defineStore('document', () => {
  const currentFile = ref(null)
  const content = ref('')
  const isLoading = ref(false)
  const error = ref(null)

  async function loadFile(file) {
    currentFile.value = file
    isLoading.value = true
    error.value = null
    try {
      const result = await window.electronAPI.readFile(file.path)
      if (result.success) {
        content.value = result.content
      } else {
        error.value = result.error
        content.value = ''
      }
    } catch (err) {
      error.value = err.message
      content.value = ''
    } finally {
      isLoading.value = false
    }
  }

  function clearContent() {
    currentFile.value = null
    content.value = ''
    error.value = null
  }

  return {
    currentFile,
    content,
    isLoading,
    error,
    loadFile,
    clearContent,
  }
})
