const { app, BrowserWindow, ipcMain, dialog, protocol, net } = require('electron')
const path = require('path')
const fs = require('fs')
const fsPromises = fs.promises
const https = require('https')
const http = require('http')
const { URL } = require('url')
const matter = require('gray-matter')
const JSZip = require('jszip')

protocol.registerSchemesAsPrivileged([
  { scheme: 'local-file', privileges: { standard: true, secure: true, supportFetchAPI: true } }
])

function makeRequest(options, data = null) {
  return new Promise((resolve, reject) => {
    const lib = options.protocol === 'https:' ? https : http
    const req = lib.request({
      ...options,
      timeout: 30000,
      headers: {
        'User-Agent': 'QBase/1.0',
        ...options.headers,
      }
    }, (res) => {
      let body = ''
      res.on('data', (chunk) => body += chunk)
      res.on('end', () => {
        try {
          const result = JSON.parse(body)
          resolve({ statusCode: res.statusCode, data: result })
        } catch (e) {
          resolve({ statusCode: res.statusCode, data: body })
        }
      })
    })

    req.on('error', (err) => {
      if (err.code === 'ECONNRESET' || err.code === 'ETIMEDOUT') {
        reject(new Error(`网络连接失败: ${err.message}。请检查网络连接或稍后重试。`))
      } else {
        reject(err)
      }
    })

    req.on('timeout', () => {
      req.destroy()
      reject(new Error('请求超时，请稍后重试。'))
    })

    if (data) req.write(JSON.stringify(data))
    req.end()
  })
}

function uploadFile(url, fileData) {
  return new Promise((resolve, reject) => {
    const parsedUrl = new URL(url)
    const options = {
      protocol: parsedUrl.protocol,
      hostname: parsedUrl.hostname,
      port: parsedUrl.port || (parsedUrl.protocol === 'https:' ? 443 : 80),
      path: parsedUrl.pathname + parsedUrl.search,
      method: 'PUT',
      timeout: 120000,
      headers: {
        'User-Agent': 'QBase/1.0',
        'Content-Length': fileData.length
      }
    }
    const lib = parsedUrl.protocol === 'https:' ? https : http
    const req = lib.request(options, (res) => {
      let body = ''
      res.on('data', (chunk) => body += chunk)
      res.on('end', () => resolve({ statusCode: res.statusCode, data: body }))
    })
    
    req.on('error', (err) => {
      if (err.code === 'ECONNRESET' || err.code === 'ETIMEDOUT') {
        reject(new Error(`文件上传失败: ${err.message}。请检查网络连接或稍后重试。`))
      } else {
        reject(err)
      }
    })
    
    req.on('timeout', () => {
      req.destroy()
      reject(new Error('文件上传超时，请稍后重试。'))
    })
    
    req.write(fileData)
    req.end()
  })
}

function downloadFile(url) {
  return new Promise((resolve, reject) => {
    const lib = url.startsWith('https') ? https : http
    lib.get(url, (res) => {
      const chunks = []
      res.on('data', (chunk) => chunks.push(chunk))
      res.on('end', () => resolve(Buffer.concat(chunks)))
    }).on('error', reject)
  })
}

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

app.whenReady().then(() => {
  createWindow()
  
  protocol.handle('local-file', (request) => {
    const filePath = request.url.slice('local-file://'.length)
    // URL 解码
    const decodedPath = decodeURIComponent(filePath)
    // 处理 Windows 路径格式
    const normalizedPath = decodedPath
      .replace(/^([a-zA-Z])(?=\/)/, '$1:') // 确保驱动器号后有冒号
      .replace(/\//g, '\\') // 转换为反斜杠
    
    try {
      // 检查文件是否存在
      if (!fs.existsSync(normalizedPath)) {
        console.error('File not found:', normalizedPath)
        return new Response('File not found', { status: 404 })
      }
      
      // 获取文件统计信息
      const stats = fs.statSync(normalizedPath)
      
      // 确定 MIME 类型
      const ext = path.extname(normalizedPath).toLowerCase()
      const mimeTypes = {
        '.pdf': 'application/pdf',
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/wav',
        '.ogg': 'audio/ogg',
        '.m4a': 'audio/mp4',
        '.flac': 'audio/flac',
        '.mp4': 'video/mp4',
        '.webm': 'video/webm',
        '.mov': 'video/quicktime',
        '.mkv': 'video/x-matroska'
      }
      const mimeType = mimeTypes[ext] || 'application/octet-stream'
      
      // 创建文件流
      const fileStream = fs.createReadStream(normalizedPath)
      
      // 返回带有正确 MIME 类型的响应
      return new Response(fileStream, {
        headers: {
          'Content-Type': mimeType,
          'Content-Length': stats.size.toString()
        }
      })
    } catch (error) {
      console.error('Error serving file:', normalizedPath, error)
      return new Response('Internal server error', { status: 500 })
    }
  })
})

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

ipcMain.handle('get-home-path', async () => {
  return app.getPath('home')
})

ipcMain.handle('fs-exists', async (event, filePath) => {
  return fs.existsSync(filePath)
})

ipcMain.handle('fs-mkdir', async (event, dirPath) => {
  return fs.mkdirSync(dirPath, { recursive: true })
})

ipcMain.handle('fs-read-file', async (event, filePath, encoding) => {
  return fs.readFileSync(filePath, encoding)
})

ipcMain.handle('fs-write-file', async (event, filePath, data, encoding) => {
  return fs.writeFileSync(filePath, data, encoding)
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
    const content = await fsPromises.readFile(filePath, 'utf-8')
    return { success: true, content }
  } catch (error) {
    return { success: false, error: error.message }
  }
})

ipcMain.handle('read-markdown', async (event, filePath) => {
  try {
    const content = await fsPromises.readFile(filePath, 'utf-8')
    const parsed = matter(content)
    return { 
      success: true, 
      content: parsed.content && parsed.content.trim() !== '' ? parsed.content : content,
      frontmatter: parsed.data
    }
  } catch (error) {
    return { success: false, error: error.message }
  }
})

ipcMain.handle('read-binary-file', async (event, filePath) => {
  try {
    const buffer = await fsPromises.readFile(filePath)
    const base64 = buffer.toString('base64')
    return { success: true, content: base64 }
  } catch (error) {
    return { success: false, error: error.message }
  }
})



ipcMain.handle('siliconflow:create-embedding', async (event, text, config) => {
  const options = {
    hostname: 'api.siliconflow.cn',
    port: 443,
    path: '/v1/embeddings',
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${config.apiKey}`
    }
  }
  const result = await makeRequest(options, {
    model: config.model || 'BAAI/bge-large-zh-v1.5',
    input: text
  })
  return result.data
})

ipcMain.handle('read-dir', async (event, dirPath) => {
  try {
    const entries = await fsPromises.readdir(dirPath, { withFileTypes: true })
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
    const stats = await fsPromises.stat(filePath)
    return { success: true, stats }
  } catch (error) {
    return { success: false, error: error.message }
  }
})

ipcMain.handle('search-files', async (event, folderPath, query) => {
  try {
    const results = []
    const searchInDir = async (dir) => {
      const entries = await fsPromises.readdir(dir, { withFileTypes: true })
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
              const content = await fsPromises.readFile(fullPath, 'utf-8')
              const parsed = matter(content)
              
              const frontmatterText = Object.values(parsed.data)
                .filter(v => v !== null && v !== undefined)
                .map(v => Array.isArray(v) ? v.join(', ') : String(v))
                .join('\n')
              
              const searchableContent = frontmatterText + '\n' + parsed.content
              const lowerContent = searchableContent.toLowerCase()
              const lowerQuery = query.toLowerCase()
              const index = lowerContent.indexOf(lowerQuery)
              
              if (index !== -1) {
                const start = Math.max(0, index - 50)
                const end = Math.min(searchableContent.length, index + query.length + 50)
                const snippet = searchableContent.slice(start, end)
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