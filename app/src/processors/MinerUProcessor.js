import { DocumentProcessor } from './DocumentProcessor.js'

export class MinerUProcessor extends DocumentProcessor {
  constructor(config) {
    super()
    this.config = config
  }

  async extractText(file) {
    if (!this.config.apiKey) {
      throw new Error('MinerU API key not configured')
    }
    const result = await window.electronAPI.mineru.extractPdf(file.path, this.config)
    return result
  }

  async extractStructured(file) {
    return await this.extractText(file)
  }
}
