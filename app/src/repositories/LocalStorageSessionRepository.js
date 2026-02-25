// app/src/repositories/LocalStorageSessionRepository.js
import { SessionRepository } from './SessionRepository'

const STORAGE_KEY = 'qbase-sessions'

export class LocalStorageSessionRepository extends SessionRepository {
  constructor() {
    super()
    this._initStorage()
  }

  _initStorage() {
    if (!localStorage.getItem(STORAGE_KEY)) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify([]))
    }
  }

  _getAllSessions() {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
  }

  _saveSessions(sessions) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions))
  }

  async getAll() {
    return this._getAllSessions()
  }

  async getById(id) {
    const sessions = this._getAllSessions()
    return sessions.find((s) => s.id === id) || null
  }

  async create(session) {
    const sessions = this._getAllSessions()
    sessions.push(session)
    this._saveSessions(sessions)
    return session
  }

  async update(id, updates) {
    const sessions = this._getAllSessions()
    const index = sessions.findIndex((s) => s.id === id)
    if (index !== -1) {
      sessions[index] = { ...sessions[index], ...updates, updatedAt: new Date().toISOString() }
      this._saveSessions(sessions)
      return sessions[index]
    }
    return null
  }

  async delete(id) {
    const sessions = this._getAllSessions()
    const filtered = sessions.filter((s) => s.id !== id)
    this._saveSessions(filtered)
  }
}
