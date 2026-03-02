import * as pdfjsLib from 'pdfjs-dist'
import pdfjsWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url'
import { MinerUProcessor } from '../MinerUProcessor.js'

pdfjsLib.GlobalWorkerOptions.workerSrc = pdfjsWorker

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
    try {
      return await this.extractPdfLocal(filePath)
    } catch (localError) {
      console.warn('本地 PDF 提取失败，尝试云端 MinerU:', localError.message)

      if (config.mineru?.apiKey) {
        try {
          return await this.extractWithMinerU(filePath, config.mineru)
        } catch (mineruError) {
          console.error('MinerU 提取也失败:', mineruError)
          throw new Error(`PDF 提取失败: ${localError.message}`)
        }
      }

      throw new Error(`PDF 提取失败: ${localError.message}`)
    }
  }

  static async extractPdfLocal(filePath) {
    try {
      const formattedPath = filePath.replace(/\\/g, '/')
      const url = `local-file://${formattedPath.replace(/^\/+/, '')}`

      const loadingTask = pdfjsLib.getDocument({ url })
      const pdfDoc = await loadingTask.promise

      let fullText = ''
      const totalPages = pdfDoc.numPages

      for (let pageNum = 1; pageNum <= totalPages; pageNum++) {
        const page = await pdfDoc.getPage(pageNum)
        const textContent = await page.getTextContent()
        const pageText = textContent.items.map((item) => item.str).join(' ')

        fullText += `--- 第 ${pageNum} 页 ---\n${pageText}\n\n`
      }

      await pdfDoc.destroy()

      return {
        text: fullText,
        fileType: 'pdf',
        extractedBy: 'local',
        extractedAt: new Date(),
        pageCount: totalPages,
        wordCount: fullText.split(/\s+/).filter(Boolean).length,
      }
    } catch (error) {
      console.error('本地 PDF 提取失败:', error)
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
