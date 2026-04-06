<script setup>
import { ref, computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useRouter } from 'vue-router'
import { Document, Search, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { usePapersStore } from '@/stores/papers'
import PaperSearchDialog from '@/components/PaperSearchDialog.vue'
import PaperList from '@/components/PaperList.vue'

const router = useRouter()
const store = usePapersStore()
const { loading } = storeToRefs(store)

const stats = computed(() => store.stats || { total_papers: 0, total_keywords: 0, recent_papers: 0 })
const searchDialogVisible = ref(false)
const paperListRefresh = ref(0)

function goBack() {
  router.push('/')
}

async function loadStats() {
  try {
    const result = await store.fetchStats()
    if (!result.success) {
      ElMessage.error(result.message || '加载统计信息失败')
    }
  } catch (error) {
    console.error('加载统计信息失败:', error)
    ElMessage.error('加载统计信息失败')
  }
}

function openSearchDialog() {
  searchDialogVisible.value = true
}

function handleSearchSaved() {
  paperListRefresh.value++
}

function handleRefresh() {
  loadStats()
  paperListRefresh.value++
}

onMounted(() => {
  loadStats()
})
</script>

<template>
  <div class="papers-view">
    <header class="header">
      <div class="header-left">
        <button class="back-btn" @click="goBack">
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
        </button>
        <h1 class="header-title">论文管理</h1>
      </div>
      <div class="header-right">
        <el-button :loading="loading" @click="handleRefresh">
          <template #icon>
            <el-icon><Refresh /></el-icon>
          </template>
          刷新
        </el-button>
      </div>
    </header>

    <div class="stats-container">
      <div class="stat-card total">
        <div class="stat-icon">
          <el-icon><Document /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.total_papers }}</div>
          <div class="stat-label">论文总数</div>
        </div>
      </div>

      <div class="stat-card authors">
        <div class="stat-icon">
          <el-icon><Document /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.total_keywords }}</div>
          <div class="stat-label">搜索关键词</div>
        </div>
      </div>

      <div class="stat-card categories">
        <div class="stat-icon">
          <el-icon><Document /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.recent_papers }}</div>
          <div class="stat-label">近7天新增</div>
        </div>
      </div>

      <div class="stat-card latest">
        <div class="stat-icon">
          <el-icon><Document /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.total_papers }}</div>
          <div class="stat-label">论文总计</div>
        </div>
      </div>
    </div>

    <div class="actions-container">
      <el-button type="primary" @click="openSearchDialog">
        <template #icon>
          <el-icon><Search /></el-icon>
        </template>
        搜索论文
      </el-button>
    </div>

    <div class="list-container">
      <PaperList :refresh="paperListRefresh" @loaded="loadStats" />
    </div>

    <PaperSearchDialog v-model="searchDialogVisible" @saved="handleSearchSaved" />
  </div>
</template>

<style scoped>
.papers-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color-page);
}

.header {
  height: 56px;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-lighter);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--el-text-color-secondary);
  transition: all 0.2s;
}

.back-btn:hover {
  background: var(--el-fill-color-lighter);
  color: var(--el-text-color-primary);
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stats-container {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  padding: 24px 24px 0 24px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: var(--el-bg-color);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.stat-card.total .stat-icon {
  background: rgba(64, 158, 255, 0.1);
  color: var(--el-color-primary);
}

.stat-card.authors .stat-icon {
  background: rgba(103, 194, 58, 0.1);
  color: var(--el-color-success);
}

.stat-card.categories .stat-icon {
  background: rgba(230, 162, 60, 0.1);
  color: var(--el-color-warning);
}

.stat-card.latest .stat-icon {
  background: rgba(245, 108, 108, 0.1);
  color: var(--el-color-danger);
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}

.actions-container {
  padding: 16px 24px;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.list-container {
  flex: 1;
  overflow: hidden;
  padding: 24px;
  background: var(--el-bg-color-page);
}
</style>
