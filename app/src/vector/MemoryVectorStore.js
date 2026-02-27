import { VectorStore } from './VectorStore.js'

function cosineSimilarity(a, b) {
  if (!a || !b || a.length !== b.length) return 0
  let dotProduct = 0
  let normA = 0
  let normB = 0
  for (let i = 0; i < a.length; i++) {
    dotProduct += a[i] * b[i]
    normA += a[i] * a[i]
    normB += b[i] * b[i]
  }
  return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB))
}

export class MemoryVectorStore extends VectorStore {
  constructor() {
    super()
    this.documents = []
    this.embeddings = []
  }

  async addDocument(doc) {
    this.documents.push(doc)
    if (doc.embedding) {
      this.embeddings.push(doc.embedding)
    }
  }

  async search(queryEmbedding, k = 5) {
    const results = []
    for (let i = 0; i < this.documents.length; i++) {
      const doc = this.documents[i]
      const embedding = this.embeddings[i]
      if (embedding) {
        const score = cosineSimilarity(queryEmbedding, embedding)
        results.push({
          id: doc.id,
          content: doc.content,
          score,
          metadata: doc.metadata,
        })
      }
    }
    return results.sort((a, b) => b.score - a.score).slice(0, k)
  }

  async clear() {
    this.documents = []
    this.embeddings = []
  }
}
