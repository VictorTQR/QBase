export class FlashcardRepository {
  async getAll() {
    throw new Error('getAll() must be implemented')
  }

  async getById(id) {
    throw new Error('getById() must be implemented')
  }

  async create(flashcardSet) {
    throw new Error('create() must be implemented')
  }

  async update(id, updates) {
    throw new Error('update() must be implemented')
  }

  async delete(id) {
    throw new Error('delete() must be implemented')
  }
}
