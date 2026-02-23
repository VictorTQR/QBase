const { contextBridge } = require('electron/renderer')

contextBridge.exposeInMainWorld('electronAPI', {
  getVersion: () => process.versions.electron,
  // 后续可添加更多通信方法
  // showDialog: (message) => ipcRenderer.invoke('show-dialog', message)
})