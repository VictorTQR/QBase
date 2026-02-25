import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { useWorkspaceStore } from './workspace'

export const useSearchStore = defineStore(
  'search',
  () => {
    const query = ref('')
    const results = ref([])
    const isLoading = ref(false)
    const error = ref(null)
    const isPanelOpen = ref(false)
    const searchScope = ref('all') // 'all' 或 folderId
    const selectedIndex = ref(0)

    const workspaceStore = useWorkspaceStore()

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

    function selectPreviousResult() {
      if (results.value.length > 0) {
        selectedIndex.value = (selectedIndex.value - 1 + results.value.length) % results.value.length
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

    async function performSearch() {
      if (!query.value.trim()) {
        results.value = []
        return
      }

      isLoading.value = true
      error.value = null
      results.value = []

      try {
        const foldersToSearch = searchScope.value === 'all'
          ? workspaceStore.folders
          : workspaceStore.folders.filter(f => f.id === searchScope.value)

        const allResults = []

        for (const folder of foldersToSearch) {
          const result = await window.electronAPI.searchFiles(folder.path, query.value)
          if (result.success) {
            allResults.push(...result.results)
          } else {
            console.error(`搜索文件夹 ${folder.name} 失败:`, result.error)
          }
        }

        results.value = allResults
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
      selectedIndex,
      hasResults,
      isSearching,
      openPanel,
      closePanel,
      setQuery,
      setSearchScope,
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
      paths: ['searchScope'],
    },
  },
)
