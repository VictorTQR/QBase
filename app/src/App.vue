<template>
  <router-view />
</template>

<script setup>
import { onMounted } from 'vue'
import { useWorkspaceStore } from '@/stores/workspace'

const workspaceStore = useWorkspaceStore()

onMounted(async () => {
  await workspaceStore.initializeFromLastWorkspace()
})
</script>
