import { RemoteBackendStrategy } from './RemoteBackendStrategy'

export class TextExtractor {
  static strategy = new RemoteBackendStrategy()
  
  static setStrategy(strategy) {
    this.strategy = strategy
  }

  static async extract(filePath, fileType, config = {}) {
    switch (fileType) {
      case 'markdown':
        return await this.extractMarkdown(filePath)
      case 'pdf':
        return await this.extractPdf(filePath, config)
      default:
        throw new Error(`不支持的文件类型: ${fileType}`)
    }
  }

  static async extractMarkdown(filePath) {
    try {
      const result = await window.electronAPI.readMarkdown(filePath)
      return {
        text: result.content || '',
        fileType: 'markdown',
        extractedBy: 'local',
        extractedAt: new Date(),
        wordCount: (result.content || '').split(/\s+/).filter(Boolean).length,
      }
    } catch (error) {
      console.error('Markdown 提取失败:', error)
      throw new Error(`Markdown 提取失败: ${error.message}`)
    }
  }

  static async extractPdf(filePath, config = {}) {
    try {
      return await this.strategy.extractPdf(filePath, config)
    } catch (error) {
      console.error('PDF 提取失败:', error)
      throw this.enhanceError(error)
    }
  }

  static enhanceError(error) {
    let errorMessage = error.message
    let suggestion = ''

    if (
      errorMessage.includes('A0202') ||
      errorMessage.includes('A0211') ||
      errorMessage.includes('API Key') ||
      errorMessage.includes('API key')
    ) {
      errorMessage = 'MinerU API Key 无效或已过期'
      suggestion = '请检查后端 .env 配置中的 MINERU_API_KEY'
    } else if (
      errorMessage.includes('ECONNREFUSED') ||
      errorMessage.includes('network') ||
      errorMessage.includes('ENOTFOUND') ||
      errorMessage.includes('连接')
    ) {
      errorMessage = '无法连接到后端服务'
      suggestion = '请确保后端服务已启动 (cd backend && uv run python -m uvicorn main:app --reload)'
    } else if (errorMessage.includes('Timeout') || errorMessage.includes('超时')) {
      errorMessage = '解析超时'
      suggestion = '请稍后重试，或尝试拆分较大的 PDF 文件'
    } else if (
      errorMessage.includes('format') ||
      errorMessage.includes('损坏') ||
      errorMessage.includes('corrupted')
    ) {
      errorMessage = 'PDF 文件格式不支持或已损坏'
      suggestion = '请尝试使用其他 PDF 文件，或修复当前文件'
    }

    const fullMessage = suggestion ? `${errorMessage}。${suggestion}` : errorMessage
    return new Error(fullMessage)
  }
}
