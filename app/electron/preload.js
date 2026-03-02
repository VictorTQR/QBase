const { contextBridge, ipcRenderer } = require('electron/renderer')

contextBridge.exposeInMainWorld('electronAPI', {
  getVersion: () => process.versions.electron,
  selectFolder: () => ipcRenderer.invoke('select-folder'),
  readFile: (filePath) => ipcRenderer.invoke('read-file', filePath),
  readMarkdown: (filePath) => ipcRenderer.invoke('read-markdown', filePath),
  readBinaryFile: (filePath) => ipcRenderer.invoke('read-binary-file', filePath),
  readDir: (dirPath) => ipcRenderer.invoke('read-dir', dirPath),
  getFileStats: (filePath) => ipcRenderer.invoke('get-file-stats', filePath),
  searchFiles: (folderPath, query) => ipcRenderer.invoke('search-files', folderPath, query),
  mineru: {
    createUploadUrls: (files, apiKey) => ipcRenderer.invoke('mineru:create-upload-urls', files, apiKey),
    uploadFile: (url, fileData) => ipcRenderer.invoke('mineru:upload-file', url, fileData),
    submitTask: (batchId, apiKey) => ipcRenderer.invoke('mineru:submit-task', batchId, apiKey),
    pollTaskStatus: (taskId, apiKey) => ipcRenderer.invoke('mineru:poll-task-status', taskId, apiKey),
    downloadResult: (url) => ipcRenderer.invoke('mineru:download-result', url),
    extractPdf: (filePath, config) => ipcRenderer.invoke('mineru:extract-pdf', filePath, config),
    testConnection: (config) => ipcRenderer.invoke('mineru:test-connection', config)
  },
  siliconflow: {
    createEmbedding: (text, config) => ipcRenderer.invoke('siliconflow:create-embedding', text, config)
  }
})