import Dexie from 'dexie'

class QBaseParseDatabase extends Dexie {
  constructor() {
    super('QBaseParse')
    this.version(1).stores({
      extractedTexts: 'filePath, type, parsedAt',
      vectors: 'filePath',
      transcripts: 'filePath',
    })
  }
}

export const db = new QBaseParseDatabase()

export class IndexedDBRepository {
  async saveExtractedText(filePath, data) {
    await db.extractedTexts.put({
      filePath,
      ...data,
      parsedAt: Date.now(),
    })
  }

  async getExtractedText(filePath) {
    return await db.extractedTexts.get(filePath)
  }

  async deleteExtractedText(filePath) {
    await db.extractedTexts.delete(filePath)
  }

  async saveVectors(filePath, vectors) {
    await db.vectors.put({
      filePath,
      vectors,
      savedAt: Date.now(),
    })
  }

  async getVectors(filePath) {
    const result = await db.vectors.get(filePath)
    return result?.vectors
  }

  async deleteVectors(filePath) {
    await db.vectors.delete(filePath)
  }

  async saveTranscript(filePath, transcript) {
    await db.transcripts.put({
      filePath,
      ...transcript,
      savedAt: Date.now(),
    })
  }

  async getTranscript(filePath) {
    return await db.transcripts.get(filePath)
  }

  async deleteTranscript(filePath) {
    await db.transcripts.delete(filePath)
  }

  async deleteAllForFile(filePath) {
    await Promise.all([
      this.deleteExtractedText(filePath),
      this.deleteVectors(filePath),
      this.deleteTranscript(filePath),
    ])
  }
}
