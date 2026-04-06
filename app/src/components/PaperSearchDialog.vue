<template>
  <el-dialog
    v-model="visible"
    title="搜索 arXiv 论文"
    width="800px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-form :model="searchForm" label-width="100px">
      <el-form-item label="搜索关键词">
        <el-input
          v-model="searchForm.keyword"
          placeholder="请输入搜索关键词，如：machine learning"
          clearable
        />
      </el-form-item>

      <el-form-item label="排序方式">
        <el-select v-model="searchForm.sortBy" placeholder="请选择排序方式">
          <el-option label="相关性" value="relevance" />
          <el-option label="最后更新日期" value="lastUpdatedDate" />
          <el-option label="提交日期" value="submittedDate" />
        </el-select>
      </el-form-item>

      <el-form-item label="结果数量">
        <el-input-number v-model="searchForm.maxResults" :min="1" :max="100" :step="10" />
      </el-form-item>

      <el-form-item>
        <el-button type="primary" :loading="searching" @click="handleSearch"> 搜索 </el-button>
        <el-button @click="handleReset">重置</el-button>
      </el-form-item>
    </el-form>

    <div v-if="searchResults.length > 0" class="search-results">
      <div class="results-header">
        <span>找到 {{ searchResults.length }} 篇论文</span>
        <el-button type="primary" size="small" :loading="saving" @click="handleSaveAll">
          保存全部
        </el-button>
      </div>

      <div class="results-list">
        <div v-for="paper in searchResults" :key="paper.arxiv_id" class="paper-item">
          <div class="paper-title">
            {{ paper.title }}
          </div>
          <div class="paper-authors">作者: {{ paper.authors.join(', ') }}</div>
          <div class="paper-abstract">
            {{ paper.summary }}
          </div>
          <div class="paper-meta">
            <span class="paper-id">{{ paper.arxiv_id }}</span>
            <span class="paper-published">{{ formatDate(paper.published) }}</span>
            <el-tag v-if="paper.primary_category" size="small" type="info">
              {{ paper.primary_category }}
            </el-tag>
          </div>
          <div class="paper-actions">
            <el-button type="primary" size="small" @click="openPdf(paper)"> 查看 PDF </el-button>
            <el-button type="success" size="small" @click="openArxiv(paper)">
              arXiv 页面
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="searched && searchResults.length === 0" class="empty-results">
      <el-empty description="未找到相关论文" />
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { ElMessage } from 'element-plus'
import { usePapersStore } from '@/stores/papers'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue', 'saved'])

const store = usePapersStore()
const { searchResults } = storeToRefs(store)
const searching = computed(() => store.searchLoading)

const visible = ref(props.modelValue)
const saving = ref(false)
const searched = ref(false)

const searchForm = reactive({
  keyword: '',
  sortBy: 'relevance',
  maxResults: 10,
})

watch(
  () => props.modelValue,
  (newVal) => {
    visible.value = newVal
  },
)

watch(visible, (newVal) => {
  emit('update:modelValue', newVal)
})

async function handleSearch() {
  if (!searchForm.keyword.trim()) {
    ElMessage.warning('请输入搜索关键词')
    return
  }

  try {
    searched.value = false
    const result = await store.searchPapers(
      searchForm.keyword,
      searchForm.maxResults,
      searchForm.sortBy,
    )

    if (result.success) {
      searched.value = true
      ElMessage.success(`找到 ${searchResults.value.length} 篇论文`)
    } else {
      ElMessage.error(result.message || '搜索失败')
    }
  } catch (error) {
    console.error('搜索论文失败:', error)
    ElMessage.error('搜索论文失败')
  }
}

function handleReset() {
  searchForm.keyword = ''
  searchForm.sortBy = 'relevance'
  searchForm.maxResults = 10
  store.clearSearchResults()
  searched.value = false
}

async function handleSaveAll() {
  if (searchResults.value.length === 0) {
    ElMessage.warning('没有可保存的论文')
    return
  }

  try {
    saving.value = true
    const result = await store.savePapers(
      searchForm.keyword,
      searchForm.maxResults,
      searchForm.sortBy,
    )

    if (result.success) {
      ElMessage.success(result.message || '保存成功')
      emit('saved')
      handleClose()
    } else {
      ElMessage.error(result.message || '保存失败')
    }
  } catch (error) {
    console.error('保存论文失败:', error)
    ElMessage.error('保存论文失败')
  } finally {
    saving.value = false
  }
}

function openPdf(paper) {
  const pdfUrl = `https://arxiv.org/pdf/${paper.arxiv_id}.pdf`
  window.open(pdfUrl, '_blank')
}

function openArxiv(paper) {
  const arxivUrl = `https://arxiv.org/abs/${paper.arxiv_id}`
  window.open(arxivUrl, '_blank')
}

function formatDate(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN')
}

function handleClose() {
  visible.value = false
  handleReset()
}
</script>

<style scoped>
.search-results {
  margin-top: 24px;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.results-header span {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.results-list {
  max-height: 500px;
  overflow-y: auto;
}

.paper-item {
  padding: 16px;
  margin-bottom: 12px;
  background: var(--el-fill-color-lighter);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
}

.paper-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 8px;
  line-height: 1.5;
}

.paper-authors {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-bottom: 8px;
}

.paper-abstract {
  font-size: 13px;
  color: var(--el-text-color-regular);
  line-height: 1.6;
  margin-bottom: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.paper-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.paper-id {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  font-family: monospace;
}

.paper-published {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.paper-actions {
  display: flex;
  gap: 8px;
}

.empty-results {
  margin-top: 24px;
}
</style>
