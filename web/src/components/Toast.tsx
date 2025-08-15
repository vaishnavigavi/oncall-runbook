import React, { useEffect } from 'react'

export interface ToastProps {
  message: string
  type: 'success' | 'error' | 'info'
  isVisible: boolean
  onClose: () => void
  duration?: number
}

const Toast: React.FC<ToastProps> = ({ 
  message, 
  type, 
  isVisible, 
  onClose, 
  duration = 5000 
}) => {
  useEffect(() => {
    if (isVisible && duration > 0) {
      const timer = setTimeout(() => {
        onClose()
      }, duration)
      return () => clearTimeout(timer)
    }
  }, [isVisible, duration, onClose])

  if (!isVisible) return null

  const baseClasses = "fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg max-w-md transition-all duration-300 ease-in-out"
  
  const typeClasses = {
    success: "bg-green-500 text-white",
    error: "bg-red-500 text-white",
    info: "bg-blue-500 text-white"
  }

  const iconClasses = {
    success: "text-green-100",
    error: "text-red-100",
    info: "text-blue-100"
  }

  return (
    <div className={`${baseClasses} ${typeClasses[type]}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className={`text-lg ${iconClasses[type]}`}>
            {type === 'success' && '✓'}
            {type === 'error' && '✕'}
            {type === 'info' && 'ℹ'}
          </div>
          <p className="text-sm font-medium">{message}</p>
        </div>
        <button
          onClick={onClose}
          className="ml-4 text-white hover:text-gray-200 focus:outline-none"
        >
          <span className="sr-only">Close</span>
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  )
}

export default Toast
