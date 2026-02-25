import { FlashcardRepository } from './FlashcardRepository'

const STORAGE_KEY = 'qbase-flashcards'

export class LocalStorageFlashcardRepository extends FlashcardRepository {
  constructor() {
    super()
  }

  _getAllData() {
    try {
      const data = localStorage.getItem(STORAGE_KEY)
      return data ? JSON.parse(data) : []
    } catch (err) {
      console.error('Failed to read flashcards from localStorage:', err)
      return []
    }
  }

  _saveAllData(data) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
    } catch (err) {
      console.error('Failed to save flashcards to localStorage:', err)
    }
  }

  async getAll() {
    return this._getAllData()
  }

  async getById(id) {
    const all = this._getAllData()
    return all.find((s) => s.id === id) || null
  }

  async create(flashcardSet) {
    const all = this._getAllData()
    all.push(flashcardSet)
    this._saveAllData(all)
    return flashcardSet
  }

  async update(id, updates) {
    const all = this._getAllData()
    const index = all.findIndex((s) => s.id === id)
    if (index !== -1) {
      all[index] = { ...all[index], ...updates, updatedAt: new Date().toISOString() }
      this._saveAllData(all)
      return all[index]
    }
    return null
  }

  async delete(id) {
    const all = this._getAllData()
    const filtered = all.filter((s) => s.id !== id)
    this._saveAllData(filtered)
  }
}
