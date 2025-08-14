import React, { useState, useRef, useEffect } from 'react'

interface ChatInputProps {
  onSendMessage: (message: string) => void
  isLoading: boolean
  placeholder?: string
}

const ChatInput: React.FC<ChatInputProps> = ({ 
  onSendMessage, 
  isLoading, 
  placeholder = "Ask a question..." 
}) => {
  const [message, setMessage] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }
  }, [message])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (message.trim() && !isLoading) {
      onSendMessage(message.trim())
      setMessage('')
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'
      }
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4">
      <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
        <div className="flex items-end space-x-3">
          {/* Textarea */}
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              disabled={isLoading}
              rows={1}
              className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 disabled:opacity-50 disabled:cursor-not-allowed min-h-[44px] max-h-32 overflow-y-auto"
              style={{ minHeight: '44px' }} // Ensure minimum touch target size
            />
            
            {/* Character count */}
            <div className="absolute bottom-2 right-2 text-xs text-gray-400 dark:text-gray-500">
              {message.length}/1000
            </div>
          </div>

          {/* Send Button */}
          <button
            type="submit"
            disabled={!message.trim() || isLoading}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 dark:disabled:bg-gray-600 text-white rounded-lg transition-colors disabled:cursor-not-allowed min-h-[44px] min-w-[44px] flex items-center justify-center"
          >
            {isLoading ? (
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
            ) : (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            )}
          </button>
        </div>

        {/* Mobile-friendly hint */}
        <div className="mt-2 text-xs text-gray-500 dark:text-gray-400 text-center sm:hidden">
          Press Enter to send, Shift+Enter for new line
        </div>

        {/* Desktop shortcuts hint */}
        <div className="mt-2 text-xs text-gray-500 dark:text-gray-400 text-center hidden sm:block">
          Press <kbd className="px-1 py-0.5 text-xs font-semibold bg-gray-200 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded">Enter</kbd> to send, <kbd className="px-1 py-0.5 text-xs font-semibold bg-gray-200 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded">Shift+Enter</kbd> for new line
        </div>
      </form>
    </div>
  )
}

export default ChatInput
