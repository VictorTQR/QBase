import { BackendStrategy } from './BackendStrategy'
import { mineruApi } from '@/utils/backend'

const POLL_INTERVAL = 3000
const MAX_POLL_ATTEMPTS = 60

export class RemoteBackendStrategy extends BackendStrategy {
  async extractPdf(filePath, config) {
    const startTime = Date.now()

    const task = await mineruApi.parseLocalFile(filePath)
    const taskId = task.id

    let result = null
    let attempts = 0

    while (attempts < MAX_POLL_ATTEMPTS) {
      const status = await mineruApi.getTaskStatus(taskId)

      if (status.state === 'done') {
        const parseResult = await mineruApi.getParseResult(taskId)
        result = parseResult.markdown_content
        break
      } else if (status.state === 'failed') {
        throw new Error(status.error || '解析任务失败')
      }

      await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL))
      attempts++
    }

    if (!result) {
      throw new Error('解析任务超时')
    }

    const duration = Date.now() - startTime

    return {
      text: result,
      fileType: 'pdf',
      extractedBy: 'mineru-backend',
      extractedAt: new Date(),
      wordCount: result.split(/\s+/).filter(Boolean).length,
      duration,
    }
  }
}
