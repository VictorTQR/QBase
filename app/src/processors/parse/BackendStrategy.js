export class BackendStrategy {
  async extractPdf(filePath, config) {
    throw new Error('extractPdf must be implemented')
  }
}
