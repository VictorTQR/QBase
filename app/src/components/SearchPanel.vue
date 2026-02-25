<template>
  <teleport to="body">
    <div v-if="searchStore.isPanelOpen" class="search-overlay" @click.self="searchStore.closePanel">
      <div class="search-panel" ref="panelRef">
        <div class="search-header">
          <el-input
            ref="inputRef"
            v-model="searchQuery"
            placeholder="搜索文件..."
            :prefix-icon="Search"
            clearable
            @input="handleInput"
            @keyup.esc="searchStore.closePanel"
            @keyup.enter="handleEnter"
            @keyup.up.prevent="searchStore.selectPreviousResult"
            @keyup.down.prevent="searchStore.selectNextResult"
            class="search-input"
          />
        </div>

        <div class="search-scope">
          <el-select v-model="searchScope" @change="handleScopeChange" size="small">
            <el-option label="所有工作区" value="all" />
            <el-option
              v-for="folder in workspaceStore.folders"
              :key="folder.id"
              :label="folder.name"
              :value="folder.id"
            />
          </el-select>
        </div>

        <div class="search-results">
          <div v-if="searchStore.isSearching" class="search-loading">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span>搜索中...</span>
          </div>

          <div v-else-if="searchStore.error" class="search-error">
            <el-icon><Warning /></el-icon>
            <span>搜索出错: {{ searchStore.error }}</span>
          </div>

          <div v-else-if="searchStore.results.length === 0 && searchStore.query" class="search-empty">
            <el-icon><Document /></el-icon>
            <span>未找到匹配的文件</span>
          </div>

          <div v-else-if="searchStore.results.length > 0" class="results-list">
            <div
              v-for="(result, index) in searchStore.results"
              :key="result.id"
              class="result-item"
              :class="{ selected: index === searchStore.selectedIndex }"
              @click="handleSelectResult(result)"
            >
              <div class="result-icon">
                <el-icon><Document /></el-icon>
              </div>
              <div class="result-content">
                <div class="result-name">
                  <span v-html="highlightText(result.name, searchStore.query)"></span>
                  <el-tag v-if="result.matchType === 'name'" size="small" type="info">文件名</el-tag>
                  <el-tag v-else size="small" type="success">内容</el-tag>
                </div>
                <div v-if="result.snippet" class="result-snippet">
                  <span v-html="highlightText(result.snippet, searchStore.query)"></span>
                </div>
                <div class="result-path">{{ result.path }}</div>
              </div>
            </div>
          </div>
        </div>

        <div class="search-footer">
          <div class="shortcut-hint">
            <span><kbd>↑</kbd><kbd>↓</kbd> 导航</span>
            <span><kbd>Enter</kbd> 打开</span>
            <span><kbd>Esc</kbd> 关闭</span>
          </div>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { Search, Loading, Warning, Document } from '@element-plus/icons-vue'
import { useSearchStore } from '@/stores/search'
import { useWorkspaceStore } from '@/stores/workspace'
import { useDocumentStore } from '@/stores/document'

function debounce(fn, delay) {
  let timer = null
  return function (...args) {
    clearTimeout(timer)
    timer = setTimeout(() => fn.apply(this, args), delay)
  }
}

const searchStore = useSearchStore()
const workspaceStore = useWorkspaceStore()
const documentStore = useDocumentStore()

const inputRef = ref(null)
const panelRef = ref(null)
const searchQuery = ref('')
const searchScope = ref(searchStore.searchScope)

const debouncedSearch = debounce(() => {
  searchStore.performSearch()
}, 300)

function handleInput() {
  searchStore.setQuery(searchQuery.value)
  debouncedSearch()
}

function handleScopeChange(value) {
  searchStore.setSearchScope(value)
  if (searchStore.query) {
    searchStore.performSearch()
  }
}

function handleEnter() {
  const selected = searchStore.getSelectedResult()
  if (selected) {
    handleSelectResult(selected)
  }
}

function handleSelectResult(result) {
  workspaceStore.selectFile(result.id)
  documentStore.loadFile(result)
  searchStore.closePanel()
}

function highlightText(text, query) {
  if (!query) return text
  const regex = new RegExp(`(${escapeRegex(query)})`, 'gi')
  return text.replace(regex, '<mark class="highlight">$1</mark>')
}

function escapeRegex(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function handleKeyDown(event) {
  if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
    event.preventDefault()
    searchStore.openPanel()
  }
}

watch(
  () => searchStore.isPanelOpen,
  async (isOpen) => {
    if (isOpen) {
      await nextTick()
      inputRef.value?.focus()
      searchQuery.value = searchStore.query
      searchScope.value = searchStore.searchScope
    }
  },
)

onMounted(() => {
  document.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeyDown)
})
</script>

<style scoped>
.search-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 100px;
  z-index: 9999;
}

.search-panel {
  width: 100%;
  max-width: 600px;
  background: var(--el-bg-color);
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  overflow: hidden;
}

.search-header {
  padding: 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.search-input :deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px var(--el-border-color) inset;
}

.search-scope {
  padding: 8px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-lighter);
}

.search-results {
  max-height: 400px;
  overflow-y: auto;
}

.search-loading,
.search-error,
.search-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 40px 16px;
  color: var(--el-text-color-secondary);
}

.results-list {
  padding: 8px 0;
}

.result-item {
  display: flex;
  gap: 12px;
  padding: 12px 16px;
  cursor: pointer;
  transition: background-color 0.15s;
}

.result-item:hover,
.result-item.selected {
  background: var(--el-fill-color-light);
}

.result-icon {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--el-text-color-secondary);
}

.result-content {
  flex: 1;
  min-width: 0;
}

.result-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
}

.result-snippet {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.result-path {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.search-footer {
  padding: 12px 16px;
  border-top: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-lighter);
}

.shortcut-hint {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}

.shortcut-hint kbd {
  display: inline-block;
  padding: 2px 6px;
  background: var(--el-bg-color-page);
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  font-family: inherit;
  font-size: 11px;
  margin-right: 4px;
}

.highlight {
  background: var(--el-color-primary-light-7);
  color: var(--el-color-primary);
  padding: 0 2px;
  border-radius: 2px;
}
</style>
