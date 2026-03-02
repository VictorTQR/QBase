import JSZip from 'jszip'
import { ElMessage } from 'element-plus'

export function generateFileName(filePath) {
  const pathParts = filePath.split(/[/\\]/)
  const fullName = pathParts[pathParts.length - 1]
  const nameWithoutExt = fullName.replace(/\.[^/.]+$/, '')
  return `${nameWithoutExt}_extracted.txt`
}

export function exportSingleText(filePath, text, customFileName = null) {
  try {
    const fileName = customFileName || generateFileName(filePath)
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = fileName
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    return true
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败: ' + (error.message || '未知错误'))
    return false
  }
}

export async function exportAllTexts(fileMap) {
  try {
    const zip = new JSZip()
    let count = 0

    for (const [filePath, data] of Object.entries(fileMap)) {
      if (data && data.text) {
        const fileName = generateFileName(filePath)
        zip.file(fileName, data.text)
        count++
      }
    }

    if (count === 0) {
      ElMessage.warning('没有可导出的文本')
      return false
    }

    const content = await zip.generateAsync({ type: 'blob' })
    const url = URL.createObjectURL(content)
    const link = document.createElement('a')
    link.href = url
    link.download = `qbase_extracted_${Date.now()}.zip`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)

    ElMessage.success(`成功导出 ${count} 个文件`)
    return true
  } catch (error) {
    console.error('批量导出失败:', error)
    ElMessage.error('批量导出失败: ' + (error.message || '未知错误'))
    return false
  }
}
