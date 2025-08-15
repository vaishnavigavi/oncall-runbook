import React from 'react'

export interface SourcesChipsProps {
  citations: string[]
  onSourceClick: (citation: string) => void
}

const SourcesChips: React.FC<SourcesChipsProps> = ({ citations, onSourceClick }) => {
  if (!citations || citations.length === 0) {
    return null
  }

  return (
    <div className="mt-4">
      <h4 className="text-sm font-medium text-gray-700 mb-2">Sources:</h4>
      <div className="flex flex-wrap gap-2">
        {citations.map((citation, index) => (
          <button
            key={index}
            onClick={() => onSourceClick(citation)}
            className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
          >
            <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
            {citation}
          </button>
        ))}
      </div>
    </div>
  )
}

export default SourcesChips

