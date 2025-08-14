import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import ChatMessage from '../components/ChatMessage'
import ChatInput from '../components/ChatInput'
import SourceDetailsPanel from '../components/SourceDetailsPanel'
import Sidebar from '../components/Sidebar'
import QuickPrompts from '../components/QuickPrompts'
import Toast from '../components/Toast'
import { askQuestion, StructuredAskResponse } from '../services/api'
import { 
  getLastSessionId, 
  setLastSessionId, 
  clearLastSessionId,
  getSessionMessages,
  exportSession
} from '../services/sessionService'

export interface Message {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
  citations?: string[]
  confidence?: number
  diagnostics?: any
}

export interface ToastState {
  message: string
  type: 'success' | 'error' | 'info'
  isVisible: boolean
}

const ChatPage: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [isDarkMode, setIsDarkMode] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  
  const [toast, setToast] = useState<ToastState>({
    message: '',
    type: 'info',
    isVisible: false
  })

  // Source details panel state
  const [isSourcePanelOpen, setIsSourcePanelOpen] = useState(false)
  const [selectedCitation, setSelectedCitation] = useState<string | null>(null)
  const [chunkContent, setChunkContent] = useState<string | null>(null)
  const [isLoadingSource, setIsLoadingSource] = useState(false)

  // Initialize session
  useEffect(() => {
    const initializeSession = async () => {
      let targetSessionId = sessionId
      
      if (!targetSessionId) {
        // Check localStorage for last session
        const lastSessionId = getLastSessionId()
        if (lastSessionId) {
          targetSessionId = lastSessionId
          navigate(`/${lastSessionId}`, { replace: true })
        } else {
          // Create new session
          await handleNewChat()
          return
        }
      }
      
      if (targetSessionId) {
        await loadSession(targetSessionId)
      }
    }

    initializeSession()
  }, [sessionId, navigate])

  const loadSession = async (sessionId: string) => {
    try {
      const response = await getSessionMessages(sessionId)
      const loadedMessages: Message[] = response.messages.map(msg => ({
        id: msg.id,
        type: msg.role as 'user' | 'assistant',
        content: msg.content,
        timestamp: new Date(msg.created_at),
        citations: msg.citations,
        confidence: msg.confidence,
        diagnostics: msg.diagnostics
      }))
      
      setMessages(loadedMessages)
      setCurrentSessionId(sessionId)
      setLastSessionId(sessionId)
      
      if (loadedMessages.length === 0) {
        // Add welcome message for new sessions
        setMessages([{
          id: '1',
          type: 'assistant',
          content: 'Hello! How can I assist you with your on-call runbook today?',
          timestamp: new Date()
        }])
      }
    } catch (error) {
      console.error('Error loading session:', error)
      showToast('Failed to load session', 'error')
    }
  }

  const handleNewChat = async () => {
    try {
      setMessages([{
        id: '1',
        type: 'assistant',
        content: 'Hello! How can I assist you with your on-call runbook today?',
        timestamp: new Date()
      }])
      setCurrentSessionId(null)
      clearLastSessionId()
      navigate('/', { replace: true })
    } catch (error) {
      console.error('Error creating new chat:', error)
      showToast('Failed to create new chat', 'error')
    }
  }

  const handleSessionSelect = async (sessionId: string) => {
    await loadSession(sessionId)
    navigate(`/${sessionId}`)
  }

  const showToast = (message: string, type: 'success' | 'error' | 'info') => {
    setToast({ message, type, isVisible: true })
  }

  const hideToast = () => {
    setToast(prev => ({ ...prev, isVisible: false }))
  }

  const handleSendMessage = async (content: string) => {
    if (!content.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: content.trim(),
      timestamp: new Date()
    }
    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)

    try {
      const response: StructuredAskResponse = await askQuestion(content.trim())

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: response.answer,
        timestamp: new Date(),
        citations: response.citations,
        confidence: response.confidence,
        diagnostics: response.diagnostics
      }

      setMessages(prev => [...prev, assistantMessage])
      
      // Update session ID if this is a new session
      if (response.session_id && !currentSessionId) {
        setCurrentSessionId(response.session_id)
        setLastSessionId(response.session_id)
        navigate(`/${response.session_id}`, { replace: true })
      }
      
      showToast('Response received successfully!', 'success')
    } catch (error) {
      console.error('Error getting response:', error)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: 'Sorry, I could not get a response from the API. Please try again later.',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
      showToast('Failed to get response from API', 'error')
    } finally {
      setIsLoading(false)
    }
  }

  const handleRegenerate = async () => {
    const lastUserMessage = messages.filter(m => m.type === 'user').pop()
    if (lastUserMessage) {
      // Remove the last assistant message
      setMessages(prev => prev.slice(0, -1))
      // Send the last user message again
      await handleSendMessage(lastUserMessage.content)
    }
  }

  const handleCopy = (content: string) => {
    showToast('Message copied to clipboard!', 'success')
  }

  const handleExport = async (content: string) => {
    if (!currentSessionId) {
      showToast('No active session to export', 'error')
      return
    }

    try {
      const response = await exportSession(currentSessionId)
      
      // Create and download the file
      const blob = new Blob([response.markdown], { type: 'text/markdown' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = response.filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      
      showToast('Session exported successfully!', 'success')
    } catch (error) {
      console.error('Error exporting session:', error)
      showToast('Failed to export session', 'error')
    }
  }

  const handleQuickPrompt = (prompt: string) => {
    handleSendMessage(prompt)
  }

  const handleSourceClick = async (citation: string) => {
    setSelectedCitation(citation)
    setIsSourcePanelOpen(true)
    setIsLoadingSource(true)
    setChunkContent(null)

    try {
      // For now, we'll show a placeholder since we don't have an API endpoint
      // to fetch individual chunk content. In a real implementation, you'd call:
      // const chunkData = await getChunkContent(citation)
      // setChunkContent(chunkData.content)

      // Simulate loading and show citation info
      setTimeout(() => {
        setChunkContent(`This is the content for citation: ${citation}\n\nIn a production system, this would fetch the actual chunk content from the FAISS index metadata.`)
        setIsLoadingSource(false)
      }, 500)
    } catch (error) {
      console.error('Error loading source content:', error)
      setChunkContent('Error loading source content')
      setIsLoadingSource(false)
      showToast('Failed to load source content', 'error')
    }
  }

  const closeSourcePanel = () => {
    setIsSourcePanelOpen(false)
    setSelectedCitation(null)
    setChunkContent(null)
  }

  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode)
  }

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen)
  }

  return (
    <div className={`flex h-screen ${isDarkMode ? 'dark' : ''}`}>
      {/* Sidebar */}
      {sidebarOpen && (
        <Sidebar
          currentSessionId={currentSessionId}
          onSessionSelect={handleSessionSelect}
          onNewChat={handleNewChat}
          isDarkMode={isDarkMode}
          onToggleDarkMode={toggleDarkMode}
        />
      )}

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <button
              onClick={toggleSidebar}
              className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <h1 className="text-lg font-semibold text-gray-900">
              {currentSessionId ? 'Chat Session' : 'New Chat'}
            </h1>
          </div>
        </div>

        {/* Chat Content */}
        <div className="flex-1 overflow-hidden flex flex-col">
          <div className="flex-1 overflow-y-auto px-6 py-4">
            {/* Quick Prompts */}
            {messages.length <= 1 && (
              <QuickPrompts onPromptSelect={handleQuickPrompt} />
            )}

            {/* Messages */}
            <div className="space-y-4">
              {messages.map((message, index) => (
                <ChatMessage
                  key={message.id}
                  message={message}
                  onSourceClick={handleSourceClick}
                  onRegenerate={handleRegenerate}
                  onCopy={handleCopy}
                  onExport={handleExport}
                  isLastMessage={index === messages.length - 1}
                />
              ))}
              
              {isLoading && (
                <div className="flex items-center space-x-2 text-gray-500">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                  <span className="text-sm">Thinking...</span>
                </div>
              )}
            </div>
          </div>

          {/* Chat Input */}
          <div className="border-t border-gray-200 px-6 py-4">
            <ChatInput onSendMessage={handleSendMessage} disabled={isLoading} />
          </div>
        </div>
      </div>

      {/* Source Details Panel */}
      <SourceDetailsPanel
        isOpen={isSourcePanelOpen}
        onClose={closeSourcePanel}
        citation={selectedCitation}
        chunkContent={chunkContent}
        isLoading={isLoadingSource}
      />

      {/* Toast Notifications */}
      <Toast
        message={toast.message}
        type={toast.type}
        isVisible={toast.isVisible}
        onClose={hideToast}
      />
    </div>
  )
}

export default ChatPage
