import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import ChatPage from './pages/ChatPage'

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<Navigate to="/new" replace />} />
          <Route path="/new" element={<ChatPage />} />
          <Route path="/:sessionId" element={<ChatPage />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
