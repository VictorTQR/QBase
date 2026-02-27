<template>
  <div class="markdown-viewer">
    <FrontmatterCard :data="frontmatter" />
    <XMarkdown :markdown="content" :enable-latex="true" :enable-breaks="true" :allow-html="false" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { XMarkdown } from 'vue-element-plus-x'
import { useDocumentStore } from '@/stores/document'
import FrontmatterCard from './FrontmatterCard.vue'

const props = defineProps({
  content: {
    type: String,
    default: '',
  },
})

const documentStore = useDocumentStore()
const frontmatter = computed(() => documentStore.frontmatter)
</script>

<style scoped>
.markdown-viewer {
  padding: 16px;
  height: 100%;
  overflow-y: auto;
}
</style>
