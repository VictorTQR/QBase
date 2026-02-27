export class VectorStore {
  async addDocument(doc) {
    throw new Error('addDocument not implemented')
  }

  async search(query, k = 5) {
    throw new Error('search not implemented')
  }

  async clear() {
    throw new Error('clear not implemented')
  }
}
