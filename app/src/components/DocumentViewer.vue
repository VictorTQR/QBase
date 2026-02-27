<template>
  <div class="document-viewer">
    <MarkdownViewer v-if="contentType === 'markdown'" :content="content" />
    <PdfViewer v-else-if="contentType === 'pdf'" :filePath="filePath" :base64Data="binaryContent" />
    <MediaViewer
      v-else-if="contentType === 'audio' || contentType === 'video'"
      :filePath="filePath"
      :base64Data="binaryContent"
      :mimeType="mimeType"
      :mediaType="contentType"
    />
    <div v-else class="unsupported">
      <el-empty description="不支持的文件格式" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useDocumentStore } from '@/stores/document'
import MarkdownViewer from './MarkdownViewer.vue'
import PdfViewer from './PdfViewer.vue'
import MediaViewer from './MediaViewer.vue'

const documentStore = useDocumentStore()

const content = computed(() => documentStore.content)
const binaryContent = computed(() => documentStore.binaryContent)
const contentType = computed(() => documentStore.contentType)
const mimeType = computed(() => documentStore.mimeType)
const filePath = computed(() => documentStore.currentFile?.path || '')
</script>

<style scoped>
.document-viewer {
  height: 100%;
  overflow: hidden;
}

.unsupported {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}
</style>
