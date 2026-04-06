import { derivativeBackendApi } from '@/api/derivativeBackend'
import { fileBackendApi } from '@/api/fileBackend'

export class FileSystemFlashcardRepository {
  constructor(workspacePath) {
    this.workspacePath = workspacePath
  }

  async _getFileHash(sourceFile) {
    // 通过文件路径获取哈希
    try {
      const result = await fileBackendApi.computeHash(sourceFile)
      return result.hash
    } catch (error) {
      console.error('获取文件哈希失败:', error)
      return null
    }
  }

  async getAll() {
    // 双写期：暂时还是从 LocalStorage 读取
    // 后续可以从文件系统扫描
    const localStorageRepo = new (
      await import('./LocalStorageFlashcardRepository')
    ).LocalStorageFlashcardRepository()
    return await localStorageRepo.getAll()
  }

  async create(set) {
    // 双写：同时写 LocalStorage 和文件系统
    const localStorageRepo = new (
      await import('./LocalStorageFlashcardRepository')
    ).LocalStorageFlashcardRepository()
    const result = await localStorageRepo.create(set)

    // 尝试写入文件系统
    if (set.sourceFile) {
      try {
        const fileHash = await this._getFileHash(set.sourceFile)
        if (fileHash) {
          const flashcardsData = {
            version: 1,
            model: null, // 后续可以记录使用的模型
            generated_at: Date.now(),
            title: set.title,
            source_file: set.sourceFile,
            cards: set.flashcards.map((card) => ({
              q: card.front,
              a: card.back,
              difficulty: card.difficulty,
              tags: [],
            })),
          }

          await derivativeBackendApi.saveDerivative(
            this.workspacePath,
            fileHash,
            'flashcards',
            flashcardsData,
          )
          console.log('闪卡已保存到文件系统')
        }
      } catch (error) {
        console.warn('闪卡保存到文件系统失败（非致命）:', error)
      }
    }

    return result
  }

  async update(setId, updates) {
    // 双写期：主要更新 LocalStorage
    const localStorageRepo = new (
      await import('./LocalStorageFlashcardRepository')
    ).LocalStorageFlashcardRepository()
    return await localStorageRepo.update(setId, updates)
  }

  async delete(setId) {
    // 双写期：主要删除 LocalStorage
    const localStorageRepo = new (
      await import('./LocalStorageFlashcardRepository')
    ).LocalStorageFlashcardRepository()
    return await localStorageRepo.delete(setId)
  }
}
