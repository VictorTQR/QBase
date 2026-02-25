import hookFetch from 'hook-fetch'
import { sseTextDecoderPlugin } from 'hook-fetch/plugins/sse'

export function createLlmApi(baseUrl, apiKey) {
  return hookFetch.create({
    baseURL: baseUrl,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${apiKey}`,
    },
    plugins: [
      sseTextDecoderPlugin({
        json: true,
        prefix: 'data: ',
        splitSeparator: '\n\n',
        lineSeparator: '\n',
        trim: true,
        doneSymbol: '[DONE]',
      }),
    ],
  })
}
