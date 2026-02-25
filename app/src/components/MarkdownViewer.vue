<template>
  <div class="markdown-viewer">
    <XMarkdown :markdown="content" :enable-latex="true" :enable-breaks="true" :allow-html="false" />
  </div>
</template>

<script setup>
import { XMarkdown } from 'vue-element-plus-x'

defineProps({
  content: {
    type: String,
    default: '',
  },
})
</script>

<style scoped>
.markdown-viewer {
  padding: 16px;
  height: 100%;
  overflow-y: auto;
}
</style>
