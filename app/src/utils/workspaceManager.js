class WorkspaceManager {
  constructor() {
    this.globalConfigDir = null
    this.workspacesFilePath = null
  }

  async init() {
    this.globalConfigDir = await this.getGlobalConfigDir()
    this.workspacesFilePath = `${this.globalConfigDir}/workspaces.json`
    await this.ensureGlobalConfigDir()
  }

  async getGlobalConfigDir() {
    const homeDir = await window.electronAPI.getHomePath()
    return `${homeDir}/.qbase`
  }

  async ensureGlobalConfigDir() {
    const exists = await window.electronAPI.fsExists(this.globalConfigDir)
    if (!exists) {
      await window.electronAPI.fsMkdir(this.globalConfigDir)
    }
  }

  async loadWorkspaces() {
    const exists = await window.electronAPI.fsExists(this.workspacesFilePath)
    if (!exists) {
      return { workspaces: [], lastWorkspace: null }
    }
    try {
      const content = await window.electronAPI.fsReadFile(this.workspacesFilePath, 'utf-8')
      return JSON.parse(content)
    } catch (error) {
      console.error('加载工作区配置失败:', error)
      return { workspaces: [], lastWorkspace: null }
    }
  }

  async saveWorkspaces(config) {
    try {
      await window.electronAPI.fsWriteFile(
        this.workspacesFilePath,
        JSON.stringify(config, null, 2),
        'utf-8'
      )
    } catch (error) {
      console.error('保存工作区配置失败:', error)
    }
  }

  async addWorkspace(workspacePath) {
    if (!workspacePath || typeof workspacePath !== 'string') {
      throw new Error('无效的工作区路径')
    }
    
    const config = await this.loadWorkspaces()
    const normalizedPath = workspacePath.replace(/\\/g, '/')
    
    const exists = config.workspaces.some(w => 
      typeof w.path === 'string' && w.path.replace(/\\/g, '/') === normalizedPath
    )
    if (!exists) {
      const name = normalizedPath.split('/').pop()
      config.workspaces.push({
        path: normalizedPath,
        name: name,
        addedAt: Date.now(),
      })
    }
    
    config.lastWorkspace = normalizedPath
    await this.saveWorkspaces(config)
    
    return config
  }

  async setLastWorkspace(workspacePath) {
    if (!workspacePath || typeof workspacePath !== 'string') {
      return
    }
    const config = await this.loadWorkspaces()
    config.lastWorkspace = workspacePath.replace(/\\/g, '/')
    await this.saveWorkspaces(config)
  }

  async getLastWorkspace() {
    const config = await this.loadWorkspaces()
    return config.lastWorkspace
  }

  async removeWorkspace(workspacePath) {
    if (!workspacePath || typeof workspacePath !== 'string') {
      throw new Error('无效的工作区路径')
    }
    
    const config = await this.loadWorkspaces()
    const normalizedPath = workspacePath.replace(/\\/g, '/')
    config.workspaces = config.workspaces.filter(w => 
      typeof w.path === 'string' && w.path.replace(/\\/g, '/') !== normalizedPath
    )
    
    if (config.lastWorkspace === normalizedPath) {
      config.lastWorkspace = config.workspaces.length > 0 ? config.workspaces[0].path : null
    }
    
    await this.saveWorkspaces(config)
    return config
  }

  async getAllWorkspaces() {
    const config = await this.loadWorkspaces()
    return config.workspaces
  }
}

export const workspaceManager = new WorkspaceManager()
