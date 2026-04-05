<template>
  <div class="paper-list">
    <div v-if="loading" class="loading-state">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>加载中...</span>
    </div>

    <div v-else-if="papers.length === 0" class="empty-state">
      <el-empty description="暂无论文数据" />
    </div>

    <div v-else class="list-content">
      <el-table :data="papers" stripe style="width: 100%">
        <el-table-column prop="title" label="标题" min-width="300">
          <template #default="{ row }">
            <div class="paper-title-cell">
              <div class="title">{{ row.title }}</div>
              <div class="authors">{{ row.authors?.join(', ') }}</div>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="arxiv_id" label="arXiv ID" width="140">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ row.arxiv_id }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="published_date" label="发布日期" width="120">
          <template #default="{ row }">
            {{ formatDate(row.published_date) }}
          </template>
        </el-table-column>

        <el-table-column prop="primary_category" label="分类" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.primary_category" size="small">
              {{ row.primary_category }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              link
              @click="openPdf(row)"
            >
              PDF
            </el-button>
            <el-button
              type="info"
              size="small"
              link
              @click="openArxiv(row)"
            >
              arXiv
            </el-button>
            <el-button
              type="success"
              size="small"
              link
              @click="showDetails(row)"
            >
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="total > 0" class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <el-dialog
      v-model="detailsVisible"
      :title="currentPaper?.title"
      width="700px"
    >
      <div v-if="currentPaper" class="paper-details">
        <div class="detail-section">
          <h4>基本信息</h4>
          <div class="detail-row">
            <span class="label">arXiv ID:</span>
            <el-tag size="small" type="info">{{ currentPaper.arxiv_id }}</el-tag>
          </div>
          <div class="detail-row">
            <span class="label">作者:</span>
            <span class="value">{{ currentPaper.authors?.join(', ') }}</span>
          </div>
          <div class="detail-row">
            <span class="label">发布日期:</span>
            <span class="value">{{ formatDate(currentPaper.published_date) }}</span>
          </div>
          <div v-if="currentPaper.primary_category" class="detail-row">
            <span class="label">分类:</span>
            <el-tag size="small">{{ currentPaper.primary_category }}</el-tag>
          </div>
        </div>

        <div class="detail-section">
          <h4>摘要</h4>
          <div class="abstract">{{ currentPaper.summary }}</div>
        </div>

        <div v-if="currentPaper.categories && currentPaper.categories.length > 0" class="detail-section">
          <h4>所有分类</h4>
          <div class="categories">
            <el-tag
              v-for="cat in currentPaper.categories"
              :key="cat"
              size="small"
              style="margin: 4px"
            >
              {{ cat }}
            </el-tag>
          </div>
        </div>

        <div class="detail-section">
          <h4>操作</h4>
          <div class="detail-actions">
            <el-button type="primary" @click="openPdf(currentPaper)">
              查看 PDF
            </el-button>
            <el-button type="info" @click="openArxiv(currentPaper)">
              访问 arXiv 页面
            </el-button>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { PapersBackendApi } from '@/api/papers'

const props = defineProps({
  refresh: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['loaded'])

const loading = ref(false)
const papers = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const detailsVisible = ref(false)
const currentPaper = ref(null)

async function loadPapers() {
  try {
    loading.value = true
    const offset = (currentPage.value - 1) * pageSize.value
    const result = await PapersBackendApi.getPaperList(offset, pageSize.value)

    if (result.success) {
      papers.value = result.data?.papers || []
      total.value = result.data?.total || 0
      emit('loaded', {
        count: papers.value.length,
        total: total.value,
      })
    } else {
      ElMessage.error(result.message || '加载论文列表失败')
    }
  } catch (error) {
    console.error('加载论文列表失败:', error)
    ElMessage.error('加载论文列表失败')
  } finally {
    loading.value = false
  }
}

function handlePageChange(page) {
  currentPage.value = page
  loadPapers()
}

function handleSizeChange(size) {
  pageSize.value = size
  currentPage.value = 1
  loadPapers()
}

function openPdf(paper) {
  const pdfUrl = `https://arxiv.org/pdf/${paper.arxiv_id}.pdf`
  window.open(pdfUrl, '_blank')
}

function openArxiv(paper) {
  const arxivUrl = `https://arxiv.org/abs/${paper.arxiv_id}`
  window.open(arxivUrl, '_blank')
}

function showDetails(paper) {
  currentPaper.value = paper
  detailsVisible.value = true
}

function formatDate(dateString) {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN')
}

watch(() => props.refresh, (newVal) => {
  if (newVal) {
    loadPapers()
  }
})

onMounted(() => {
  loadPapers()
})

defineExpose({
  loadPapers,
})
</script>

<style scoped>
.paper-list {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  gap: 12px;
  color: var(--el-text-color-secondary);
}

.loading-state .el-icon {
  font-size: 32px;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 300px;
}

.list-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.paper-title-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.paper-title-cell .title {
  font-weight: 500;
  color: var(--el-text-color-primary);
  line-height: 1.4;
}

.paper-title-cell .authors {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pagination-container {
  display: flex;
  justify-content: center;
  padding: 16px 0;
  border-top: 1px solid var(--el-border-color-lighter);
  background: var(--el-bg-color);
}

.paper-details {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.detail-section h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.detail-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.detail-row .label {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  min-width: 80px;
}

.detail-row .value {
  font-size: 14px;
  color: var(--el-text-color-primary);
  flex: 1;
}

.abstract {
  font-size: 14px;
  line-height: 1.6;
  color: var(--el-text-color-regular);
  padding: 12px;
  background: var(--el-fill-color-lighter);
  border-radius: 4px;
}

.categories {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.detail-actions {
  display: flex;
  gap: 12px;
}
</style>
