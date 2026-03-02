import { MinerUProcessor } from '../MinerUProcessor.js'

export class TextExtractor {
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
    if (!config.mineru?.apiKey) {
      throw new Error('PDF 文本提取需要配置 MinerU API Key，请在设置中完成配置')
    }

    try {
      return await this.extractWithMinerU(filePath, config.mineru)
    } catch (error) {
      console.error('MinerU PDF 提取失败:', error)
      throw error
    }
  }

  static async extractWithMinerU(filePath, mineruConfig) {
    try {
      const processor = new MinerUProcessor(mineruConfig)
      const result = await processor.extractText({ path: filePath })

      return {
        text: result,
        fileType: 'pdf',
        extractedBy: 'mineru',
        extractedAt: new Date(),
        wordCount: result.split(/\s+/).filter(Boolean).length,
      }
    } catch (error) {
      console.error('MinerU 提取失败:', error)

      let errorMessage = error.message
      let suggestion = ''

      if (
        errorMessage.includes('A0202') ||
        errorMessage.includes('A0211') ||
        errorMessage.includes('API Key') ||
        errorMessage.includes('API key')
      ) {
        errorMessage = 'MinerU API Key 无效或已过期'
        suggestion = '请在设置中检查您的 API Key 是否正确'
      } else if (
        errorMessage.includes('ECONNRESET') ||
        errorMessage.includes('network') ||
        errorMessage.includes('ENOTFOUND') ||
        errorMessage.includes('连接')
      ) {
        errorMessage = 'MinerU 网络连接失败'
        suggestion = '请检查网络连接或稍后重试'
      } else if (errorMessage.includes('Timeout') || errorMessage.includes('超时')) {
        errorMessage = 'MinerU 解析超时'
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
      throw new Error(fullMessage)
    }
  }
}
