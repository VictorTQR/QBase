import { useParseConfigStore } from '@/stores/parseConfig'
import { audioApi } from '@/utils/backend'

const POLL_INTERVAL = 3000
const MAX_POLL_ATTEMPTS = 600

export class AudioTranscriber {
  static async transcribe(filePath) {
    const parseConfigStore = useParseConfigStore()
    const { asrModel } = parseConfigStore.audioConfig

    try {
      const result = await audioApi.transcribeAudio(filePath, { model: asrModel })
      return await this._pollTask(result.task_id)
    } catch (error) {
      console.error('音频转录失败:', error)
      throw error
    }
  }

  static async _pollTask(taskId) {
    let attempts = 0

    while (attempts < MAX_POLL_ATTEMPTS) {
      const task = await audioApi.getTaskStatus(taskId)

      if (task.status === 'completed') {
        return {
          text: task.transcription || '',
          segments: [],
        }
      }

      if (task.status === 'failed') {
        throw new Error(task.error || '转录失败')
      }

      await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL))
      attempts++
    }

    throw new Error('转录超时')
  }
}
