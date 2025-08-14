import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface AskResponse {
  answer: string
  sources: string[]
  confidence: number
}

export interface StructuredAskResponse {
  answer: string
  citations: string[]
  trace_id: string
  retrieved_chunks: number
  confidence: number
}

export const askQuestion = async (question: string): Promise<StructuredAskResponse> => {
  try {
    const response = await api.post('/ask/structured', {
      question,
      context: ''
    })
    return response.data
  } catch (error) {
    console.error('Error asking question:', error)
    throw new Error('Failed to get response from API')
  }
}

export const askQuestionLegacy = async (question: string): Promise<AskResponse> => {
  try {
    const response = await api.post('/ask', {
      question,
      context: ''
    })
    return response.data
  } catch (error) {
    console.error('Error asking question:', error)
    throw new Error('Failed to get response from API')
  }
}

export const checkHealth = async (): Promise<boolean> => {
  try {
    const response = await api.get('/health')
    return response.data.status === 'ok'
  } catch (error) {
    console.error('Health check failed:', error)
    return false
  }
}

export default api
