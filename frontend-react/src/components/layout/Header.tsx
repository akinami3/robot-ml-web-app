import { useEffect, useState } from 'react'
import { NavLink } from 'react-router-dom'
import { useConnectionStore } from '../../stores/connectionStore'
import api from '../../services/api'
import './Header.css'

const Header = () => {
  const { mqttConnected, websocketConnected, startMonitoring, stopMonitoring } = useConnectionStore()
  const [simulatorRunning, setSimulatorRunning] = useState(false)

  useEffect(() => {
    startMonitoring()
    return () => {
      stopMonitoring()
    }
  }, [startMonitoring, stopMonitoring])

  const handleStartSimulator = async () => {
    try {
      await api.post('/api/v1/robot/simulator/start')
      setSimulatorRunning(true)
    } catch (error) {
      console.error('Failed to start simulator:', error)
      alert('シミュレータの起動に失敗しました')
    }
  }

  const handleStopSimulator = async () => {
    try {
      await api.post('/api/v1/robot/simulator/stop')
      setSimulatorRunning(false)
    } catch (error) {
      console.error('Failed to stop simulator:', error)
      alert('シミュレータの停止に失敗しました')
    }
  }

  return (
    <header className="header">
      <div className="header-content">
        <h1 className="title">Robot ML Web App - React</h1>
        
        <nav className="nav">
          <NavLink to="/robot-control" className="nav-link">ロボット制御</NavLink>
          <NavLink to="/database" className="nav-link">データベース</NavLink>
          <NavLink to="/machine-learning" className="nav-link">機械学習</NavLink>
          <NavLink to="/chatbot" className="nav-link">チャットボット</NavLink>
        </nav>

        <div className="header-actions">
          <button 
            onClick={handleStartSimulator} 
            className="btn btn-primary" 
            disabled={simulatorRunning}
          >
            シミュレーション起動
          </button>
          <button 
            onClick={handleStopSimulator} 
            className="btn btn-danger" 
            disabled={!simulatorRunning}
          >
            シミュレーション終了
          </button>

          <div className="status-indicators">
            <div className={`status-item ${mqttConnected ? 'connected' : ''}`}>
              <span className="status-dot"></span>
              <span className="status-label">MQTT</span>
            </div>
            <div className={`status-item ${websocketConnected ? 'connected' : ''}`}>
              <span className="status-dot"></span>
              <span className="status-label">WS</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}

export default Header
