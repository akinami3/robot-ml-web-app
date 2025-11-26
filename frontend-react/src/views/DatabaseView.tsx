import { useState, useEffect, useRef } from 'react'
import { config } from '../config'
import api from '../services/api'
import './Views.css'

const DatabaseView = () => {
  const [isRecording, setIsRecording] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const [recordedData, setRecordedData] = useState<any[]>([])
  const [recordOptions, setRecordOptions] = useState({
    recordPosition: true,
    recordOrientation: true,
    recordBattery: true,
    recordCamera: false,
  })
  
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    if (isRecording && !wsRef.current) {
      const wsUrl = `${config.wsUrl}/api/v1/ws/database`
      const ws = new WebSocket(wsUrl)

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        if (data.type === 'recorded_data') {
          setRecordedData(prev => [...prev, data.data])
        }
      }

      wsRef.current = ws
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, [isRecording])

  const handleStartRecording = async () => {
    try {
      await api.post('/api/v1/database/recording/start', {
        record_position: recordOptions.recordPosition,
        record_orientation: recordOptions.recordOrientation,
        record_battery: recordOptions.recordBattery,
        record_camera: recordOptions.recordCamera,
      })
      setIsRecording(true)
      setIsPaused(false)
      setRecordedData([])
    } catch (error) {
      console.error('Failed to start recording:', error)
      alert('Failed to start recording')
    }
  }

  const handlePauseRecording = async () => {
    try {
      await api.post('/api/v1/database/recording/pause')
      setIsPaused(true)
    } catch (error) {
      console.error('Failed to pause recording:', error)
    }
  }

  const handleSaveRecording = async () => {
    try {
      await api.post('/api/v1/database/recording/save')
      alert('Recording saved successfully')
      handleEndRecording()
    } catch (error) {
      console.error('Failed to save recording:', error)
    }
  }

  const handleDiscardRecording = async () => {
    if (!confirm('Are you sure you want to discard the recording?')) return
    
    try {
      await api.post('/api/v1/database/recording/discard')
      handleEndRecording()
    } catch (error) {
      console.error('Failed to discard recording:', error)
    }
  }

  const handleEndRecording = async () => {
    try {
      await api.post('/api/v1/database/recording/stop')
      setIsRecording(false)
      setIsPaused(false)
    } catch (error) {
      console.error('Failed to end recording:', error)
    }
  }

  return (
    <div className="view database-view">
      <div className="view-header">
        <h1>Database</h1>
        <p className="subtitle">Record and manage robot data</p>
      </div>

      <div className="panel">
        <h2>Recording Controls</h2>
        
        <div className="data-options">
          <div className="checkbox-group">
            <input
              type="checkbox"
              id="recordPosition"
              checked={recordOptions.recordPosition}
              onChange={(e) => setRecordOptions({...recordOptions, recordPosition: e.target.checked})}
            />
            <label htmlFor="recordPosition">Position</label>
          </div>
          <div className="checkbox-group">
            <input
              type="checkbox"
              id="recordOrientation"
              checked={recordOptions.recordOrientation}
              onChange={(e) => setRecordOptions({...recordOptions, recordOrientation: e.target.checked})}
            />
            <label htmlFor="recordOrientation">Orientation</label>
          </div>
          <div className="checkbox-group">
            <input
              type="checkbox"
              id="recordBattery"
              checked={recordOptions.recordBattery}
              onChange={(e) => setRecordOptions({...recordOptions, recordBattery: e.target.checked})}
            />
            <label htmlFor="recordBattery">Battery</label>
          </div>
          <div className="checkbox-group">
            <input
              type="checkbox"
              id="recordCamera"
              checked={recordOptions.recordCamera}
              onChange={(e) => setRecordOptions({...recordOptions, recordCamera: e.target.checked})}
            />
            <label htmlFor="recordCamera">Camera Images</label>
          </div>
        </div>

        <div className="recording-controls">
          <button onClick={handleStartRecording} className="btn btn-primary" disabled={isRecording}>
            開始
          </button>
          <button onClick={handlePauseRecording} className="btn btn-secondary" disabled={!isRecording || isPaused}>
            一時停止
          </button>
          <button onClick={handleSaveRecording} className="btn btn-success" disabled={!isRecording}>
            保存
          </button>
          <button onClick={handleDiscardRecording} className="btn btn-danger" disabled={!isRecording}>
            破棄
          </button>
          <button onClick={handleEndRecording} className="btn btn-secondary" disabled={!isRecording}>
            終了
          </button>
        </div>

        {isRecording && (
          <div className="recording-status">
            <p>Recording in progress... {recordedData.length} records</p>
          </div>
        )}
      </div>

      <div className="panel">
        <h2>Recorded Data</h2>
        <table className="data-table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Position X</th>
              <th>Position Y</th>
              <th>Orientation</th>
              <th>Battery</th>
            </tr>
          </thead>
          <tbody>
            {recordedData.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center' }}>No data recorded</td>
              </tr>
            ) : (
              recordedData.slice(-10).map((record, index) => (
                <tr key={index}>
                  <td>{new Date(record.timestamp).toLocaleTimeString()}</td>
                  <td>{record.position_x?.toFixed(2) || '-'}</td>
                  <td>{record.position_y?.toFixed(2) || '-'}</td>
                  <td>{record.orientation ? (record.orientation * 180 / Math.PI).toFixed(1) + '°' : '-'}</td>
                  <td>{record.battery_level || '-'}%</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default DatabaseView
