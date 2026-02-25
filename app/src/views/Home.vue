<template>
  <MainLayout>
    <Sidebar />
    <ContentPane />
    <AgentPanel />
  </MainLayout>
</template>

<script setup>
import MainLayout from '@/components/Layout/MainLayout.vue'
import Sidebar from '@/components/Layout/Sidebar.vue'
import ContentPane from '@/components/Layout/ContentPane.vue'
import AgentPanel from '@/components/Layout/AgentPanel.vue'
</script>

<style scoped></style>
