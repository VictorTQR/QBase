const { app, BrowserWindow, ipcMain, dialog } = require('electron')
const path = require('path')
const fs = require('fs').promises

const supportedExtensions = [
  '.md',
  '.pdf',
  '.mp3', '.wav', '.ogg', '.m4a', '.flac',
  '.mp4', '.webm', '.mov', '.mkv'
]

function getFileType(fileName) {
  const ext = path.extname(fileName).toLowerCase()
  if (ext === '.md') return 'markdown'
  if (ext === '.pdf') return 'pdf'
  if (['.mp3', '.wav', '.ogg', '.m4a', '.flac'].includes(ext)) return 'audio'
  if (['.mp4', '.webm', '.mov', '.mkv'].includes(ext)) return 'video'
  return 'unknown'
}

// 判断是否为开发环境
const isDev = process.env.NODE_ENV === 'development'

function createWindow() {
  const win = new BrowserWindow({
    width: 800,
    height: 600,
    autoHideMenuBar: true,
    webPreferences: {
      // 安全配置：启用上下文隔离，禁用 Node.js 集成
      contextIsolation: true,
      nodeIntegration: false,
      // 指定预加载脚本
      preload: path.join(__dirname, 'preload.js')
    }
  })

  // 开发环境：加载 Vue 开发服务器地址
  if (isDev) {
    win.loadURL('http://localhost:5173')
    win.webContents.openDevTools()
  } else {
    // 生产环境：加载打包后的文件
    win.loadFile(path.join(__dirname, '../dist/index.html'))
  }
}

app.whenReady().then(createWindow)

// macOS 特殊处理
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})
app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow()
  }
})

ipcMain.handle('select-folder', async () => {
  const result = await dialog.showOpenDialog({
    properties: ['openDirectory', 'createDirectory']
  })
  if (!result.canceled && result.filePaths.length > 0) {
    const folderPath = result.filePaths[0]
    const folderName = path.basename(folderPath)
    return { path: folderPath, name: folderName }
  }
  return null
})

ipcMain.handle('read-file', async (event, filePath) => {
  try {
    const content = await fs.readFile(filePath, 'utf-8')
    return { success: true, content }
  } catch (error) {
    return { success: false, error: error.message }
  }
})

ipcMain.handle('read-binary-file', async (event, filePath) => {
  try {
    const buffer = await fs.readFile(filePath)
    const base64 = buffer.toString('base64')
    return { success: true, content: base64 }
  } catch (error) {
    return { success: false, error: error.message }
  }
})

ipcMain.handle('read-dir', async (event, dirPath) => {
  try {
    const entries = await fs.readdir(dirPath, { withFileTypes: true })
    const files = []
    const folders = []
    for (const entry of entries) {
      if (entry.isDirectory()) {
        folders.push({
          id: `${dirPath}/${entry.name}`,
          name: entry.name,
          path: path.join(dirPath, entry.name),
          type: 'folder',
          children: []
        })
      } else if (entry.isFile()) {
        const ext = path.extname(entry.name).toLowerCase()
        if (supportedExtensions.includes(ext)) {
          files.push({
            id: `${dirPath}/${entry.name}`,
            name: entry.name,
            path: path.join(dirPath, entry.name),
            type: 'file',
            fileType: getFileType(entry.name)
          })
        }
      }
    }
    return { success: true, folders, files }
  } catch (error) {
    return { success: false, error: error.message }
  }
})

ipcMain.handle('get-file-stats', async (event, filePath) => {
  try {
    const stats = await fs.stat(filePath)
    return { success: true, stats }
  } catch (error) {
    return { success: false, error: error.message }
  }
})

ipcMain.handle('search-files', async (event, folderPath, query) => {
  try {
    const results = []
    const searchInDir = async (dir) => {
      const entries = await fs.readdir(dir, { withFileTypes: true })
      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name)
        if (entry.isDirectory()) {
          await searchInDir(fullPath)
        } else if (entry.isFile()) {
          const ext = path.extname(entry.name).toLowerCase()
          if (supportedExtensions.includes(ext)) {
            if (entry.name.toLowerCase().includes(query.toLowerCase())) {
              results.push({
                id: fullPath,
                name: entry.name,
                path: fullPath,
                type: 'file',
                fileType: getFileType(entry.name),
                matchType: 'name',
                snippet: ''
              })
            } else if (ext === '.md') {
              const content = await fs.readFile(fullPath, 'utf-8')
              const lowerContent = content.toLowerCase()
              const lowerQuery = query.toLowerCase()
              const index = lowerContent.indexOf(lowerQuery)
              if (index !== -1) {
                const start = Math.max(0, index - 50)
                const end = Math.min(content.length, index + query.length + 50)
                const snippet = content.slice(start, end)
                results.push({
                  id: fullPath,
                  name: entry.name,
                  path: fullPath,
                  type: 'file',
                  fileType: getFileType(entry.name),
                  matchType: 'content',
                  snippet: snippet
                })
              }
            }
          }
        }
      }
    }
    await searchInDir(folderPath)
    return { success: true, results }
  } catch (error) {
    return { success: false, error: error.message }
  }
})