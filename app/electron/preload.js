const { contextBridge, ipcRenderer } = require('electron/renderer')

contextBridge.exposeInMainWorld('electronAPI', {
  getVersion: () => process.versions.electron,
  getHomePath: () => ipcRenderer.invoke('get-home-path'),
  fsExists: (filePath) => ipcRenderer.invoke('fs-exists', filePath),
  fsMkdir: (dirPath) => ipcRenderer.invoke('fs-mkdir', dirPath),
  fsReadFile: (filePath, encoding) => ipcRenderer.invoke('fs-read-file', filePath, encoding),
  fsWriteFile: (filePath, data, encoding) => ipcRenderer.invoke('fs-write-file', filePath, data, encoding),
  selectFolder: () => ipcRenderer.invoke('select-folder'),
  readFile: (filePath) => ipcRenderer.invoke('read-file', filePath),
  readMarkdown: (filePath) => ipcRenderer.invoke('read-markdown', filePath),
  readBinaryFile: (filePath) => ipcRenderer.invoke('read-binary-file', filePath),
  readDir: (dirPath) => ipcRenderer.invoke('read-dir', dirPath),
  getFileStats: (filePath) => ipcRenderer.invoke('get-file-stats', filePath),
  searchFiles: (folderPath, query) => ipcRenderer.invoke('search-files', folderPath, query),
  siliconflow: {
    createEmbedding: (text, config) => ipcRenderer.invoke('siliconflow:create-embedding', text, config)
  }
})