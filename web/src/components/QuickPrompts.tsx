import React from 'react'

interface QuickPromptsProps {
  onPromptSelect: (prompt: string) => void
}

const QuickPrompts: React.FC<QuickPromptsProps> = ({ onPromptSelect }) => {
  const prompts = [
    {
      title: "High CPU Usage",
      description: "Investigate high CPU usage alerts",
      prompt: "High CPU usage alert 80% for 5 minutes, what should I check first?"
    },
    {
      title: "Memory Issues",
      description: "Troubleshoot memory problems",
      prompt: "Memory usage alert 85% for 10 minutes, what are the first steps?"
    },
    {
      title: "Payment Errors",
      description: "Handle payment gateway issues",
      prompt: "Payment gateway errors, customers can't complete transactions"
    },
    {
      title: "Database Performance",
      description: "Investigate database issues",
      prompt: "Database query performance issues, slow response times"
    },
    {
      title: "Network Problems",
      description: "Troubleshoot network connectivity",
      prompt: "Network connectivity issues, services can't reach each other"
    },
    {
      title: "Deployment Issues",
      description: "Handle deployment problems",
      prompt: "Recent deployment caused increased error rates"
    }
  ]

  return (
    <div className="mb-6">
      <h3 className="text-sm font-medium text-gray-700 mb-3">Quick Prompts</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {prompts.map((prompt, index) => (
          <button
            key={index}
            onClick={() => onPromptSelect(prompt.prompt)}
            className="text-left p-3 bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-lg transition-colors group"
          >
            <div className="font-medium text-sm text-gray-900 group-hover:text-blue-600">
              {prompt.title}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {prompt.description}
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}

export default QuickPrompts

