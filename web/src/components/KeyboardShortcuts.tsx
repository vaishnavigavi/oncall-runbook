import React, { useEffect, useState } from 'react'

interface KeyboardShortcutsProps {
  onNewChat?: () => void
  onToggleSidebar?: () => void
  onFocusInput?: () => void
  onToggleTheme?: () => void
}

const KeyboardShortcuts: React.FC<KeyboardShortcutsProps> = ({
  onNewChat,
  onToggleSidebar,
  onFocusInput,
  onToggleTheme
}) => {
  const [showShortcuts, setShowShortcuts] = useState(false)

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Don't trigger shortcuts when typing in input fields
      if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) {
        return
      }

      // Ctrl/Cmd + K: Focus input
      if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
        event.preventDefault()
        onFocusInput?.()
      }

      // Ctrl/Cmd + N: New chat
      if ((event.ctrlKey || event.metaKey) && event.key === 'n') {
        event.preventDefault()
        onNewChat?.()
      }

      // Ctrl/Cmd + B: Toggle sidebar
      if ((event.ctrlKey || event.metaKey) && event.key === 'b') {
        event.preventDefault()
        onToggleSidebar?.()
      }

      // Ctrl/Cmd + J: Toggle theme
      if ((event.ctrlKey || event.metaKey) && event.key === 'j') {
        event.preventDefault()
        onToggleTheme?.()
      }

      // ?: Show shortcuts
      if (event.key === '?') {
        event.preventDefault()
        setShowShortcuts(prev => !prev)
      }

      // Escape: Hide shortcuts
      if (event.key === 'Escape') {
        setShowShortcuts(false)
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [onNewChat, onToggleSidebar, onFocusInput, onToggleTheme])

  if (!showShortcuts) {
    return null
  }

  const shortcuts = [
    { key: '⌘/Ctrl + K', description: 'Focus chat input' },
    { key: '⌘/Ctrl + N', description: 'Start new chat' },
    { key: '⌘/Ctrl + B', description: 'Toggle sidebar' },
    { key: '⌘/Ctrl + J', description: 'Toggle theme' },
    { key: '?', description: 'Show/hide shortcuts' },
    { key: 'Esc', description: 'Close shortcuts' }
  ]

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 z-50"
        onClick={() => setShowShortcuts(false)}
      />
      
      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="bg-white dark:bg-gray-900 rounded-lg shadow-xl max-w-md w-full max-h-[80vh] overflow-y-auto">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Keyboard Shortcuts
            </h3>
            <button
              onClick={() => setShowShortcuts(false)}
              className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Content */}
          <div className="p-4 space-y-3">
            {shortcuts.map((shortcut, index) => (
              <div key={index} className="flex items-center justify-between py-2">
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {shortcut.description}
                </span>
                <kbd className="px-2 py-1 text-xs font-semibold text-gray-800 dark:text-gray-200 bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded">
                  {shortcut.key}
                </kbd>
              </div>
            ))}
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
            <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
              Press <kbd className="px-1 py-0.5 text-xs font-semibold bg-gray-200 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded">?</kbd> anytime to show shortcuts
            </p>
          </div>
        </div>
      </div>
    </>
  )
}

export default KeyboardShortcuts
