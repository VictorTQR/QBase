import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { useWorkspaceStore } from './workspace'
import { useVectorStore } from './vector'

export const useSearchStore = defineStore(
  'search',
  () => {
    const query = ref('')
    const results = ref([])
    const isLoading = ref(false)
    const error = ref(null)
    const isPanelOpen = ref(false)
    const searchScope = ref('all')
    const searchMode = ref('fulltext')
    const selectedIndex = ref(0)

    const workspaceStore = useWorkspaceStore()
    const vectorStore = useVectorStore()

    const hasResults = computed(() => results.value.length > 0)
    const isSearching = computed(() => isLoading.value && query.value.length > 0)

    function openPanel() {
      isPanelOpen.value = true
      selectedIndex.value = 0
    }

    function closePanel() {
      isPanelOpen.value = false
      query.value = ''
      results.value = []
      error.value = null
      selectedIndex.value = 0
    }

    function setQuery(newQuery) {
      query.value = newQuery
      selectedIndex.value = 0
    }

    function setSearchScope(scope) {
      searchScope.value = scope
    }

    function setSearchMode(mode) {
      searchMode.value = mode
    }

    function selectPreviousResult() {
      if (results.value.length > 0) {
        selectedIndex.value =
          (selectedIndex.value - 1 + results.value.length) % results.value.length
      }
    }

    function selectNextResult() {
      if (results.value.length > 0) {
        selectedIndex.value = (selectedIndex.value + 1) % results.value.length
      }
    }

    function getSelectedResult() {
      return results.value[selectedIndex.value] || null
    }

    async function performFulltextSearch() {
      const foldersToSearch =
        searchScope.value === 'all'
          ? workspaceStore.folders
          : workspaceStore.folders.filter((f) => f.id === searchScope.value)

      const allResults = []

      for (const folder of foldersToSearch) {
        const result = await window.electronAPI.searchFiles(folder.path, query.value)
        if (result.success) {
          allResults.push(...result.results)
        } else {
          console.error(`搜索文件夹 ${folder.name} 失败:`, result.error)
        }
      }

      return allResults
    }

    async function performVectorSearch() {
      const workspaceId = searchScope.value === 'all' ? null : searchScope.value
      const response = await vectorStore.searchVectors(query.value, 10, workspaceId)

      return response.results.map((r) => ({
        id: r.file_path,
        name: r.file_name,
        path: r.file_path,
        snippet: r.content,
        matchType: 'vector',
        score: r.score,
        chunkIndex: r.chunk_index,
      }))
    }

    async function performHybridSearch() {
      const [fulltextResults, vectorResults] = await Promise.all([
        performFulltextSearch(),
        performVectorSearch(),
      ])

      const merged = new Map()

      fulltextResults.forEach((r) => {
        merged.set(r.id, { ...r, ftScore: 1 })
      })

      vectorResults.forEach((r) => {
        const existing = merged.get(r.id)
        if (existing) {
          existing.score = (existing.score || 0) + r.score * 0.7
          existing.snippet = existing.snippet || r.snippet
        } else {
          merged.set(r.id, { ...r, score: r.score * 0.7 })
        }
      })

      return Array.from(merged.values()).sort(
        (a, b) => (b.score || b.ftScore) - (a.score || a.ftScore),
      )
    }

    async function performSearch() {
      if (!query.value.trim()) {
        results.value = []
        return
      }

      isLoading.value = true
      error.value = null
      results.value = []

      try {
        if (searchMode.value === 'vector') {
          results.value = await performVectorSearch()
        } else if (searchMode.value === 'hybrid') {
          results.value = await performHybridSearch()
        } else {
          results.value = await performFulltextSearch()
        }
      } catch (err) {
        error.value = err.message
        console.error('搜索失败:', err)
      } finally {
        isLoading.value = false
      }
    }

    function clearResults() {
      results.value = []
      error.value = null
      selectedIndex.value = 0
    }

    return {
      query,
      results,
      isLoading,
      error,
      isPanelOpen,
      searchScope,
      searchMode,
      selectedIndex,
      hasResults,
      isSearching,
      openPanel,
      closePanel,
      setQuery,
      setSearchScope,
      setSearchMode,
      selectPreviousResult,
      selectNextResult,
      getSelectedResult,
      performSearch,
      clearResults,
    }
  },
  {
    persist: {
      key: 'qbase-search',
      paths: ['searchScope', 'searchMode'],
    },
  },
)
