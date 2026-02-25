import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { LocalStorageFlashcardRepository } from '@/repositories/LocalStorageFlashcardRepository'
import { useAgentStore } from './agent'
import { useDocumentStore } from './document'

function generateId() {
  const array = new Uint8Array(16)
  crypto.getRandomValues(array)
  array[6] = (array[6] & 0x0f) | 0x40
  array[8] = (array[8] & 0x3f) | 0x80
  return [...array]
    .map((b, i) =>
      [4, 6, 8, 10].includes(i)
        ? '-' + b.toString(16).padStart(2, '0')
        : b.toString(16).padStart(2, '0'),
    )
    .join('')
}

export const useFlashcardStore = defineStore('flashcard', () => {
  const repository = new LocalStorageFlashcardRepository()

  const flashcardSets = ref([])
  const currentSetId = ref(null)
  const currentCardIndex = ref(0)
  const isFlipped = ref(false)
  const isGenerating = ref(false)
  const generateError = ref(null)
  const viewMode = ref('list')

  const currentSet = computed(() => {
    return flashcardSets.value.find((s) => s.id === currentSetId.value) || null
  })

  const currentCard = computed(() => {
    if (!currentSet.value) return null
    return currentSet.value.flashcards[currentCardIndex.value] || null
  })

  const progress = computed(() => {
    if (!currentSet.value) return { current: 0, total: 0 }
    return {
      current: currentCardIndex.value + 1,
      total: currentSet.value.flashcards.length,
    }
  })

  async function loadSets() {
    flashcardSets.value = await repository.getAll()
  }

  async function selectSet(setId) {
    currentSetId.value = setId
    currentCardIndex.value = 0
    isFlipped.value = false
  }

  async function deleteSet(setId) {
    await repository.delete(setId)
    flashcardSets.value = flashcardSets.value.filter((s) => s.id !== setId)
    if (currentSetId.value === setId) {
      currentSetId.value = flashcardSets.value.length > 0 ? flashcardSets.value[0].id : null
      currentCardIndex.value = 0
    }
  }

  async function generateFlashcards(count = 10) {
    const documentStore = useDocumentStore()
    const agentStore = useAgentStore()

    if (!documentStore.currentFile || !documentStore.content) {
      generateError.value = '请先打开一个 Markdown 文档'
      return
    }

    isGenerating.value = true
    generateError.value = null

    try {
      const result = await agentStore.generateFlashcards(documentStore.content, count)
      if (result.success) {
        const flashcards = result.flashcards.map((card) => ({
          id: generateId(),
          front: card.front,
          back: card.back,
          difficulty: card.difficulty || 'medium',
          mastered: false,
          lastReviewed: null,
          createdAt: new Date().toISOString(),
        }))

        const set = {
          id: generateId(),
          title: documentStore.currentFile.name.replace('.md', ''),
          sourceFile: documentStore.currentFile.path,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          flashcards,
        }

        await repository.create(set)
        flashcardSets.value.push(set)
        currentSetId.value = set.id
        currentCardIndex.value = 0
        isFlipped.value = false
        viewMode.value = 'view'
      } else {
        generateError.value = result.error
      }
    } catch (err) {
      generateError.value = err.message
    } finally {
      isGenerating.value = false
    }
  }

  function flipCard() {
    isFlipped.value = !isFlipped.value
  }

  function nextCard() {
    if (!currentSet.value) return
    if (currentCardIndex.value < currentSet.value.flashcards.length - 1) {
      currentCardIndex.value++
      isFlipped.value = false
    }
  }

  function prevCard() {
    if (currentCardIndex.value > 0) {
      currentCardIndex.value--
      isFlipped.value = false
    }
  }

  async function markMastered(cardId) {
    if (!currentSet.value) return
    const card = currentSet.value.flashcards.find((c) => c.id === cardId)
    if (card) {
      card.mastered = true
      card.lastReviewed = new Date().toISOString()
      await repository.update(currentSetId.value, {
        flashcards: currentSet.value.flashcards,
      })
    }
  }

  loadSets()

  return {
    flashcardSets,
    currentSetId,
    currentSet,
    currentCardIndex,
    currentCard,
    isFlipped,
    isGenerating,
    generateError,
    viewMode,
    progress,
    loadSets,
    selectSet,
    deleteSet,
    generateFlashcards,
    flipCard,
    nextCard,
    prevCard,
    markMastered,
  }
})
