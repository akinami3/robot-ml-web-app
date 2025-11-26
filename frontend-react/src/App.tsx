import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Header from './components/layout/Header'
import RobotControlView from './views/RobotControlView'
import DatabaseView from './views/DatabaseView'
import MLView from './views/MLView'
import ChatbotView from './views/ChatbotView'
import './App.css'

function App() {
  return (
    <Router>
      <div className="app">
        <Header />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Navigate to="/robot-control" replace />} />
            <Route path="/robot-control" element={<RobotControlView />} />
            <Route path="/database" element={<DatabaseView />} />
            <Route path="/machine-learning" element={<MLView />} />
            <Route path="/chatbot" element={<ChatbotView />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
