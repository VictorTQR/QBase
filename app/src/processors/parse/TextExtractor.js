import { ParseBackendApi } from '@/api/parseBackend'

export class TextExtractor {
  static async extract(filePath) {
    try {
      const duplicateCheck = await ParseBackendApi.checkDuplicate({ file_path: filePath })

      if (duplicateCheck.is_duplicate && duplicateCheck.existing_task) {
        const task = duplicateCheck.existing_task
        if (task.markdown_content) {
          return {
            success: true,
            markdown: task.markdown_content,
            taskId: task.id,
            isCached: true,
          }
        } else {
          const result = await ParseBackendApi.getTaskResult(task.id)
          return {
            success: true,
            markdown: result.markdown_content,
            taskId: task.id,
            isCached: true,
          }
        }
      }

      const task = await ParseBackendApi.parseLocalFile(filePath)

      if (task.is_duplicate) {
        if (task.markdown_content) {
          return {
            success: true,
            markdown: task.markdown_content,
            taskId: task.id,
            isCached: true,
          }
        }
      }

      const pollResult = await TextExtractor.pollTaskUntilDone(task.id)
      if (pollResult.success) {
        const result = await ParseBackendApi.getTaskResult(task.id)
        return {
          success: true,
          markdown: result.markdown_content,
          taskId: task.id,
        }
      } else {
        return {
          success: false,
          error: pollResult.error,
        }
      }
    } catch (error) {
      console.error('文本提取失败:', error)
      return {
        success: false,
        error: error.message,
      }
    }
  }

  static async pollTaskUntilDone(taskId, interval = 3000, maxAttempts = 600) {
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      const task = await ParseBackendApi.getTask(taskId)
      if (task.state === 'done') {
        return { success: true, task }
      } else if (task.state === 'failed') {
        return { success: false, error: task.error_msg, task }
      }
      await new Promise((resolve) => setTimeout(resolve, interval))
    }
    return { success: false, error: '超时' }
  }
}
