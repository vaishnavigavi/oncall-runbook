import React, { useState } from 'react'

interface DiagnosticsData {
  logs?: string[]
  queue_depth?: number
  [key: string]: any
}

interface CollapsibleDiagnosticsProps {
  diagnostics: DiagnosticsData | null
  isVisible: boolean
}

const CollapsibleDiagnostics: React.FC<CollapsibleDiagnosticsProps> = ({
  diagnostics,
  isVisible
}) => {
  const [isExpanded, setIsExpanded] = useState(false)

  if (!isVisible || !diagnostics) {
    return null
  }

  const hasContent = Object.values(diagnostics).some(value => 
    value !== null && value !== undefined && value !== ''
  )

  if (!hasContent) {
    return null
  }

  const formatCode = (content: string) => {
    // Simple code formatting - could be enhanced with syntax highlighting
    return content
      .split('\n')
      .map((line, index) => (
        <div key={index} className="font-mono text-sm">
          {line}
        </div>
      ))
  }

  const renderDiagnosticItem = (key: string, value: any) => {
    if (value === null || value === undefined || value === '') {
      return null
    }

    let content
    let icon

    switch (key) {
      case 'logs':
        icon = (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        )
        content = (
          <div className="space-y-2">
            {Array.isArray(value) ? value.map((log, index) => (
              <div key={index} className="bg-gray-50 dark:bg-gray-800 rounded p-2">
                {formatCode(log)}
              </div>
            )) : (
              <div className="bg-gray-50 dark:bg-gray-800 rounded p-2">
                {formatCode(String(value))}
              </div>
            )}
          </div>
        )
        break

      case 'queue_depth':
        icon = (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
        )
        content = (
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded p-3">
            <span className="text-blue-700 dark:text-blue-300 font-medium">
              Queue Depth: {value}
            </span>
          </div>
        )
        break

      default:
        icon = (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
        content = (
          <div className="bg-gray-50 dark:bg-gray-800 rounded p-2">
            {typeof value === 'string' ? formatCode(value) : JSON.stringify(value, null, 2)}
          </div>
        )
    }

    return (
      <div key={key} className="space-y-2">
        <div className="flex items-center space-x-2 text-sm font-medium text-gray-700 dark:text-gray-300">
          {icon}
          <span className="capitalize">{key.replace(/_/g, ' ')}</span>
        </div>
        {content}
      </div>
    )
  }

  return (
    <div className="mt-4 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors flex items-center justify-between text-left"
      >
        <div className="flex items-center space-x-2">
          <svg className="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 012 2v6a2 2 0 002 2h2a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2z" />
          </svg>
          <span className="font-medium text-gray-900 dark:text-white">Diagnostics</span>
          <span className="text-xs text-gray-500 dark:text-gray-400 bg-gray-200 dark:bg-gray-700 px-2 py-1 rounded">
            {Object.keys(diagnostics).filter(key => 
              diagnostics[key] !== null && diagnostics[key] !== undefined && diagnostics[key] !== ''
            ).length} items
          </span>
        </div>
        <svg 
          className={`w-5 h-5 text-gray-500 dark:text-gray-400 transition-transform ${
            isExpanded ? 'rotate-180' : ''
          }`} 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Content */}
      {isExpanded && (
        <div className="px-4 py-3 bg-white dark:bg-gray-900 space-y-4">
          {Object.entries(diagnostics).map(([key, value]) => 
            renderDiagnosticItem(key, value)
          )}
        </div>
      )}
    </div>
  )
}

export default CollapsibleDiagnostics

