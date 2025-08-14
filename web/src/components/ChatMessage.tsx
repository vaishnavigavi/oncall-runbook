import React, { useState } from 'react'
import SourcesChips from './SourcesChips'

export interface Message {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
  citations?: string[]
  confidence?: number
  diagnostics?: any
}

interface ChatMessageProps {
  message: Message
  onSourceClick: (citation: string) => void
  onRegenerate?: () => void
  onCopy?: (content: string) => void
  onExport?: (content: string) => void
  isLastMessage?: boolean
}

const ChatMessage: React.FC<ChatMessageProps> = ({ 
  message, 
  onSourceClick, 
  onRegenerate, 
  onCopy, 
  onExport,
  isLastMessage = false
}) => {
  const [showActions, setShowActions] = useState(false)
  const isUser = message.type === 'user'

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content)
      if (onCopy) onCopy(message.content)
    } catch (error) {
      console.error('Failed to copy:', error)
    }
  }

  const handleExport = () => {
    if (onExport) onExport(message.content)
  }

  return (
    <div 
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4 group`}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      <div className={`max-w-3xl ${isUser ? 'order-2' : 'order-1'} relative`}>
        <div className={`rounded-lg px-4 py-3 ${
          isUser
            ? 'bg-blue-600 text-white'
            : 'bg-white text-gray-900 border border-gray-200'
        }`}>
          <div className="flex items-start space-x-3">
            {!isUser && (
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                  <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                </div>
              </div>
            )}

            <div className="flex-1 min-w-0">
              <div className="text-sm">
                {isUser ? 'You' : 'OnCall Assistant'}
              </div>

              <div className={`mt-1 text-sm ${
                isUser ? 'text-white' : 'text-gray-800'
              }`}>
                {message.content}
              </div>

              {/* Sources for assistant messages */}
              {!isUser && message.citations && message.citations.length > 0 && (
                <SourcesChips
                  citations={message.citations}
                  onSourceClick={onSourceClick}
                />
              )}

              {/* Confidence score for assistant messages */}
              {!isUser && message.confidence && (
                <div className="mt-2 text-xs text-gray-500">
                  Confidence: {(message.confidence * 100).toFixed(1)}%
                </div>
              )}
            </div>

            {isUser && (
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        {!isUser && showActions && (
          <div className="absolute -top-2 right-2 flex items-center space-x-1 bg-white border border-gray-200 rounded-lg shadow-lg px-2 py-1 opacity-0 group-hover:opacity-100 transition-opacity">
            {onRegenerate && isLastMessage && (
              <button
                onClick={onRegenerate}
                className="p-1 text-gray-600 hover:text-blue-600 transition-colors"
                title="Regenerate response"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </button>
            )}
            
            {onCopy && (
              <button
                onClick={handleCopy}
                className="p-1 text-gray-600 hover:text-green-600 transition-colors"
                title="Copy message"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </button>
            )}
            
            {onExport && (
              <button
                onClick={handleExport}
                className="p-1 text-gray-600 hover:text-purple-600 transition-colors"
                title="Export message"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </button>
            )}
          </div>
        )}

        <div className={`text-xs text-gray-500 mt-1 ${
          isUser ? 'text-right' : 'text-left'
        }`}>
          {message.timestamp.toLocaleTimeString()}
        </div>
      </div>
    </div>
  )
}

export default ChatMessage
