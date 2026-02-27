import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

function getFileType(fileName) {
  const ext = fileName.split('.').pop().toLowerCase()
  if (ext === 'md') return 'markdown'
  if (ext === 'pdf') return 'pdf'
  if (['mp3', 'wav', 'ogg', 'm4a', 'flac'].includes(ext)) return 'audio'
  if (['mp4', 'webm', 'mov', 'mkv'].includes(ext)) return 'video'
  return 'unknown'
}

function getMimeType(fileType) {
  const mimes = {
    pdf: 'application/pdf',
    mp3: 'audio/mpeg',
    wav: 'audio/wav',
    ogg: 'audio/ogg',
    m4a: 'audio/mp4',
    flac: 'audio/flac',
    mp4: 'video/mp4',
    webm: 'video/webm',
    mov: 'video/quicktime',
  }
  return mimes[fileType] || 'application/octet-stream'
}

export const useDocumentStore = defineStore('document', () => {
  const currentFile = ref(null)
  const content = ref('')
  const binaryContent = ref(null)
  const contentType = ref('markdown')
  const mimeType = ref('')
  const isLoading = ref(false)
  const error = ref(null)

  const isBinaryFile = computed(() => ['pdf', 'audio', 'video'].includes(contentType.value))

  async function loadFile(file) {
    currentFile.value = file
    isLoading.value = true
    error.value = null
    content.value = ''
    binaryContent.value = null

    const fileType = file.fileType || getFileType(file.name)
    contentType.value = fileType
    mimeType.value = getMimeType(fileType)

    try {
      if (!isBinaryFile.value) {
        const result = await window.electronAPI.readFile(file.path)
        if (result.success) {
          content.value = result.content
        } else {
          error.value = result.error
        }
      }
    } catch (err) {
      error.value = err.message
    } finally {
      isLoading.value = false
    }
  }

  function clearContent() {
    currentFile.value = null
    content.value = ''
    binaryContent.value = null
    contentType.value = 'markdown'
    mimeType.value = ''
    error.value = null
  }

  return {
    currentFile,
    content,
    binaryContent,
    contentType,
    mimeType,
    isLoading,
    error,
    isBinaryFile,
    loadFile,
    clearContent,
  }
})
