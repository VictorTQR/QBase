const STORAGE_KEY = 'qbase-parse-index'

export class LocalStorageParseIndexRepository {
  async getAll() {
    const data = localStorage.getItem(STORAGE_KEY)
    return data ? JSON.parse(data) : {}
  }

  async save(index) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(index))
  }

  async update(filePath, updates) {
    const index = await this.getAll()
    index[filePath] = { ...index[filePath], ...updates }
    await this.save(index)
  }

  async delete(filePath) {
    const index = await this.getAll()
    delete index[filePath]
    await this.save(index)
  }

  async clear() {
    localStorage.removeItem(STORAGE_KEY)
  }
}
