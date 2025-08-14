import React, { useState, useEffect } from 'react'
import { Session, listSessions, createSession, updateSession, deleteSession } from '../services/sessionService'

interface SidebarProps {
  currentSessionId: string | null
  onSessionSelect: (sessionId: string) => void
  onNewChat: () => void
  isDarkMode: boolean
  onToggleDarkMode: () => void
}

interface KBStatus {
  docs_count: number
  index_ready: boolean
  docs: Array<{ filename: string; hash: string }>
}

const Sidebar: React.FC<SidebarProps> = ({
  currentSessionId,
  onSessionSelect,
  onNewChat,
  isDarkMode,
  onToggleDarkMode
}) => {
  const [sessions, setSessions] = useState<Session[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null)
  const [editingTitle, setEditingTitle] = useState('')
  const [kbStatus, setKbStatus] = useState<KBStatus | null>(null)
  const [kbLoading, setKbLoading] = useState(true)

  // Fetch KB status on component mount
  useEffect(() => {
    fetchKBStatus()
  }, [])

  // Load sessions when search term changes
  useEffect(() => {
    loadSessions()
  }, [searchTerm])

  const fetchKBStatus = async () => {
    try {
      setKbLoading(true)
      const response = await fetch(`${import.meta.env.VITE_API_BASE || 'http://localhost:8000'}/kb/status`)
      if (response.ok) {
        const data = await response.json()
        setKbStatus(data)
      } else {
        console.warn('Failed to fetch KB status')
        setKbStatus(null)
      }
    } catch (error) {
      console.error('Error fetching KB status:', error)
      setKbStatus(null)
    } finally {
      setKbLoading(false)
    }
  }

  const loadSessions = async () => {
    try {
      setIsLoading(true)
      const response = await listSessions(searchTerm)
      setSessions(response.sessions)
    } catch (error) {
      console.error('Error loading sessions:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSearch = (term: string) => {
    setSearchTerm(term)
  }

  const handleNewChat = () => {
    onNewChat()
  }

  const handleSessionSelect = (sessionId: string) => {
    onSessionSelect(sessionId)
  }

  const handleEditSession = (session: Session) => {
    setEditingSessionId(session.id)
    setEditingTitle(session.title)
  }

  const handleSaveEdit = async (sessionId: string) => {
    try {
      await updateSession(sessionId, { title: editingTitle })
      setEditingSessionId(null)
      setEditingTitle('')
      loadSessions()
    } catch (error) {
      console.error('Error updating session:', error)
    }
  }

  const handleCancelEdit = () => {
    setEditingSessionId(null)
    setEditingTitle('')
  }

  const handleDeleteSession = async (sessionId: string) => {
    if (window.confirm('Are you sure you want to delete this session? This action cannot be undone.')) {
      try {
        await deleteSession(sessionId)
        loadSessions()
        if (currentSessionId === sessionId) {
          onNewChat()
        }
      } catch (error) {
        console.error('Error deleting session:', error)
      }
    }
  }

  const refreshKBStatus = () => {
    fetchKBStatus()
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (!files || files.length === 0) return

    try {
      setIsLoading(true)
      
      const results = []
      let successCount = 0
      let errorCount = 0
      
      // Upload each file individually since the API accepts one file at a time
      for (let i = 0; i < files.length; i++) {
        const file = files[i]
        const formData = new FormData()
        formData.append('file', file)
        
        try {
          const response = await fetch(`${import.meta.env.VITE_API_BASE || 'http://localhost:8000'}/kb/ingest`, {
            method: 'POST',
            body: formData
          })

          if (response.ok) {
            const result = await response.json()
            results.push({ file: file.name, success: true, result })
            successCount++
          } else {
            const error = await response.text()
            results.push({ file: file.name, success: false, error })
            errorCount++
          }
        } catch (error) {
          results.push({ file: file.name, success: false, error: 'Network error' })
          errorCount++
        }
      }
      
      // Refresh KB status to show new documents
      await fetchKBStatus()
      
      // Show results
      if (successCount > 0 && errorCount === 0) {
        alert(`Successfully uploaded ${successCount} document(s)`)
      } else if (successCount > 0 && errorCount > 0) {
        alert(`Uploaded ${successCount} document(s), ${errorCount} failed. Check console for details.`)
      } else {
        alert(`Upload failed for all ${errorCount} document(s). Check console for details.`)
      }
      
      console.log('Upload results:', results)
      
    } catch (error) {
      console.error('Error uploading files:', error)
      alert('Error uploading files. Please try again.')
    } finally {
      setIsLoading(false)
      // Reset the file input
      event.target.value = ''
    }
  }

  const handleDragOver = (event: React.DragEvent) => {
    event.preventDefault()
    event.currentTarget.classList.add('border-blue-400', 'bg-blue-50')
  }

  const handleDragLeave = (event: React.DragEvent) => {
    event.preventDefault()
    event.currentTarget.classList.remove('border-blue-400', 'bg-blue-50')
  }

  const handleDrop = (event: React.DragEvent) => {
    event.preventDefault()
    event.currentTarget.classList.remove('border-blue-400', 'bg-blue-50')
    
    const files = event.dataTransfer.files
    if (files.length > 0) {
      // Create a fake event to reuse the upload logic
      const fakeEvent = {
        target: { files, value: '' }
      } as React.ChangeEvent<HTMLInputElement>
      handleFileUpload(fakeEvent)
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60)
    
    if (diffInHours < 24) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    } else if (diffInHours < 168) { // 7 days
      return date.toLocaleDateString([], { weekday: 'short' })
    } else {
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' })
    }
  }

  return (
    <div className={`w-80 h-full bg-gray-50 border-r border-gray-200 flex flex-col ${isDarkMode ? 'dark' : ''}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Chat Sessions</h2>
          <button
            onClick={onToggleDarkMode}
            className="p-2 rounded-lg hover:bg-gray-200 transition-colors"
            title={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {isDarkMode ? (
              <svg className="w-5 h-5 text-yellow-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clipRule="evenodd" />
              </svg>
            ) : (
              <svg className="w-5 h-5 text-gray-600" fill="currentColor" viewBox="0 0 20 20">
                <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
              </svg>
            )}
          </button>
        </div>
        
        {/* KB Status Pill */}
        <div className="mb-4">
          {kbLoading ? (
            <div className="flex items-center space-x-2 px-3 py-2 bg-gray-100 rounded-lg">
              <svg className="w-4 h-4 animate-spin text-gray-500" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span className="text-sm text-gray-500">Loading KB status...</span>
            </div>
          ) : kbStatus ? (
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 px-3 py-2 bg-blue-50 border border-blue-200 rounded-lg">
                <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
                </svg>
                <span className="text-sm font-medium text-blue-700">
                  Using {kbStatus.docs_count} docs
                </span>
                {kbStatus.index_ready ? (
                  <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                )}
                <span className="text-xs text-blue-600">
                  {kbStatus.index_ready ? 'index ready' : 'index building'}
                </span>
              </div>
              <button
                onClick={refreshKBStatus}
                className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                title="Refresh KB status"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </button>
            </div>
          ) : (
            <div className="flex items-center space-x-2 px-3 py-2 bg-gray-100 rounded-lg">
              <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              <span className="text-sm text-gray-500">KB status unavailable</span>
            </div>
          )}
        </div>
        
        {/* Upload Section */}
        <div className="mb-4">
          <div 
            className="border-2 border-dashed border-gray-300 rounded-lg p-4 hover:border-blue-400 transition-colors"
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <div className="text-center">
              <svg className="mx-auto h-8 w-8 text-gray-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <p className="text-sm text-gray-600 mb-2">
                <span className="font-medium text-blue-600">Click to upload</span> or drag and drop
              </p>
              <p className="text-xs text-gray-500 mb-3">
                Supports .md, .txt, .pdf, .log files
              </p>
              <input
                type="file"
                multiple
                accept=".md,.txt,.pdf,.log"
                onChange={handleFileUpload}
                className="hidden"
                id="file-upload"
              />
              <label
                htmlFor="file-upload"
                className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 cursor-pointer transition-colors"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Upload Documents
              </label>
            </div>
          </div>
        </div>
        
        {/* New Chat Button */}
        <button
          onClick={handleNewChat}
          className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center space-x-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          <span>New Chat</span>
        </button>
      </div>

      {/* Search */}
      <div className="p-4 border-b border-gray-200">
        <div className="relative">
          <input
            type="text"
            placeholder="Search sessions..."
            value={searchTerm}
            onChange={(e) => handleSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <svg className="absolute left-3 top-2.5 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center p-4">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
          </div>
        ) : sessions.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            {searchTerm ? 'No sessions found' : 'No sessions yet'}
          </div>
        ) : (
          <div className="p-2">
            {sessions.map((session) => (
              <div
                key={session.id}
                className={`group relative p-3 rounded-lg mb-2 cursor-pointer transition-colors ${
                  currentSessionId === session.id
                    ? 'bg-blue-100 border border-blue-200'
                    : 'hover:bg-gray-100'
                }`}
                onClick={() => handleSessionSelect(session.id)}
              >
                {/* Session Title */}
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    {editingSessionId === session.id ? (
                      <input
                        type="text"
                        value={editingTitle}
                        onChange={(e) => setEditingTitle(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') handleSaveEdit(session.id)
                          if (e.key === 'Escape') handleCancelEdit()
                        }}
                        className="w-full px-2 py-1 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        autoFocus
                      />
                    ) : (
                      <h3 className="text-sm font-medium text-gray-900 truncate">
                        {session.title}
                      </h3>
                    )}
                    
                    {/* Session Info */}
                    <div className="flex items-center space-x-2 mt-1 text-xs text-gray-500">
                      <span>{session.message_count} messages</span>
                      <span>•</span>
                      <span>{formatDate(session.updated_at)}</span>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    {editingSessionId === session.id ? (
                      <>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleSaveEdit(session.id)
                          }}
                          className="p-1 text-green-600 hover:text-green-700"
                          title="Save"
                        >
                          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleCancelEdit()
                          }}
                          className="p-1 text-gray-600 hover:text-gray-700"
                          title="Cancel"
                        >
                          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                          </svg>
                        </button>
                      </>
                    ) : (
                      <>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleEditSession(session)
                          }}
                          className="p-1 text-gray-600 hover:text-gray-700"
                          title="Edit title"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                          </svg>
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleDeleteSession(session.id)
                          }}
                          className="p-1 text-red-600 hover:text-red-700"
                          title="Delete session"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default Sidebar
