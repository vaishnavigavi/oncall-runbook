import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

export interface Session {
  id: string
  title: string
  description?: string
  created_at: string
  updated_at: string
  message_count: number
}

export interface SessionCreate {
  title: string
  description?: string
}

export interface SessionUpdate {
  title?: string
  description?: string
}

export interface Message {
  id: string
  session_id: string
  content: string
  role: 'user' | 'assistant'
  created_at: string
  citations?: string[]
  confidence?: number
  diagnostics?: any
}

export interface SessionListResponse {
  sessions: Session[]
  total: number
}

export interface MessageListResponse {
  messages: Message[]
  total: number
  session_id: string
}

export interface ExportResponse {
  markdown: string
  filename: string
}

// Session Management
export const createSession = async (session: SessionCreate): Promise<Session> => {
  try {
    const response = await api.post('/sessions', session)
    return response.data
  } catch (error) {
    console.error('Error creating session:', error)
    throw new Error('Failed to create session')
  }
}

export const listSessions = async (search?: string, limit: number = 50, offset: number = 0): Promise<SessionListResponse> => {
  try {
    const params = new URLSearchParams()
    if (search) params.append('search', search)
    params.append('limit', limit.toString())
    params.append('offset', offset.toString())
    
    const response = await api.get(`/sessions?${params.toString()}`)
    return response.data
  } catch (error) {
    console.error('Error listing sessions:', error)
    throw new Error('Failed to list sessions')
  }
}

export const getSession = async (sessionId: string): Promise<Session> => {
  try {
    const response = await api.get(`/sessions/${sessionId}`)
    return response.data
  } catch (error) {
    console.error('Error getting session:', error)
    throw new Error('Failed to get session')
  }
}

export const updateSession = async (sessionId: string, updates: SessionUpdate): Promise<Session> => {
  try {
    const response = await api.patch(`/sessions/${sessionId}`, updates)
    return response.data
  } catch (error) {
    console.error('Error updating session:', error)
    throw new Error('Failed to update session')
  }
}

export const deleteSession = async (sessionId: string): Promise<void> => {
  try {
    await api.delete(`/sessions/${sessionId}`)
  } catch (error) {
    console.error('Error deleting session:', error)
    throw new Error('Failed to delete session')
  }
}

// Message Management
export const getSessionMessages = async (sessionId: string, limit: number = 100, offset: number = 0): Promise<MessageListResponse> => {
  try {
    const params = new URLSearchParams()
    params.append('limit', limit.toString())
    params.append('offset', offset.toString())
    
    const response = await api.get(`/sessions/${sessionId}/messages?${params.toString()}`)
    return response.data
  } catch (error) {
    console.error('Error getting session messages:', error)
    throw new Error('Failed to get session messages')
  }
}

// Export
export const exportSession = async (sessionId: string): Promise<ExportResponse> => {
  try {
    const response = await api.post(`/sessions/${sessionId}/export`)
    return response.data
  } catch (error) {
    console.error('Error exporting session:', error)
    throw new Error('Failed to export session')
  }
}

// Local Storage Management
export const getLastSessionId = (): string | null => {
  return localStorage.getItem('lastSessionId')
}

export const setLastSessionId = (sessionId: string): void => {
  localStorage.setItem('lastSessionId', sessionId)
}

export const clearLastSessionId = (): void => {
  localStorage.removeItem('lastSessionId')
}
