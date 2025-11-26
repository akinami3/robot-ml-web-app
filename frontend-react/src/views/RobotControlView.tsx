import { useState, useEffect, useRef } from 'react'
import { config } from '../config'
import api from '../services/api'
import nipplejs from 'nipplejs'
import './Views.css'

interface RobotStatus {
  position_x: number
  position_y: number
  orientation: number
  battery_level: number
  is_moving: boolean
}

const RobotControlView = () => {
  const [robotStatus, setRobotStatus] = useState<RobotStatus | null>(null)
  const [cameraImage, setCameraImage] = useState('')
  const [isNavigating, setIsNavigating] = useState(false)
  const [goalX, setGoalX] = useState(0)
  const [goalY, setGoalY] = useState(0)
  const [goalOrientation, setGoalOrientation] = useState(0)
  
  const wsRef = useRef<WebSocket | null>(null)
  const joystickRef = useRef<HTMLDivElement>(null)
  const managerRef = useRef<any>(null)

  useEffect(() => {
    // WebSocket setup
    const wsUrl = `${config.wsUrl}/api/v1/ws/robot`
    const ws = new WebSocket(wsUrl)

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'robot_status') {
        setRobotStatus(data.data)
      } else if (data.type === 'camera_image') {
        setCameraImage(data.data.image)
      } else if (data.type === 'navigation_status') {
        setIsNavigating(data.data.status === 'active')
      }
    }

    wsRef.current = ws

    // Joystick setup
    if (joystickRef.current && !managerRef.current) {
      const manager = nipplejs.create({
        zone: joystickRef.current,
        mode: 'static',
        position: { left: '50%', top: '50%' },
        color: '#2563eb',
        size: 150,
      })

      manager.on('move', (_evt: any, data: any) => {
        const force = data.force
        const angle = data.angle.radian
        const vx = Math.cos(angle) * force
        const vy = Math.sin(angle) * force
        
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({
            type: 'velocity_command',
            data: { vx, vy, vz: 0, angular: 0 },
          }))
        }
      })

      manager.on('end', () => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({
            type: 'velocity_command',
            data: { vx: 0, vy: 0, vz: 0, angular: 0 },
          }))
        }
      })

      managerRef.current = manager
    }

    return () => {
      if (ws) ws.close()
      if (managerRef.current) {
        managerRef.current.destroy()
        managerRef.current = null
      }
    }
  }, [])

  const handleSetGoal = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await api.post('/api/v1/robot/control/navigate', {
        target_x: goalX,
        target_y: goalY,
        target_orientation: (goalOrientation * Math.PI) / 180,
      })
      setIsNavigating(true)
    } catch (error) {
      alert('Failed to set navigation goal')
    }
  }

  const handleCancelGoal = async () => {
    try {
      await api.delete('/api/v1/robot/control/navigate')
      setIsNavigating(false)
    } catch (error) {
      alert('Failed to cancel navigation')
    }
  }

  const getBatteryColor = (level: number) => {
    if (level > 60) return 'green'
    if (level > 30) return 'orange'
    return 'red'
  }

  return (
    <div className="view robot-control-view">
      <div className="view-header">
        <h1>Robot Control</h1>
        <p className="subtitle">Control the robot and monitor its status in real-time</p>
      </div>

      <div className="control-grid">
        <div className="panel">
          <h2>Robot Status</h2>
          {robotStatus ? (
            <div className="status-info">
              <div className="status-item-row">
                <span className="label">Position X:</span>
                <span className="value">{robotStatus.position_x.toFixed(2)} m</span>
              </div>
              <div className="status-item-row">
                <span className="label">Position Y:</span>
                <span className="value">{robotStatus.position_y.toFixed(2)} m</span>
              </div>
              <div className="status-item-row">
                <span className="label">Orientation:</span>
                <span className="value">{(robotStatus.orientation * 180 / Math.PI).toFixed(1)}°</span>
              </div>
              <div className="status-item-row">
                <span className="label">Battery:</span>
                <span className="value" style={{ color: getBatteryColor(robotStatus.battery_level) }}>
                  {robotStatus.battery_level}%
                </span>
              </div>
              <div className="status-item-row">
                <span className="label">Moving:</span>
                <span className="value">{robotStatus.is_moving ? 'Yes' : 'No'}</span>
              </div>
            </div>
          ) : (
            <div className="no-status">
              <p>No robot status available</p>
            </div>
          )}
        </div>

        <div className="panel camera-feed">
          {cameraImage ? (
            <img src={`data:image/jpeg;base64,${cameraImage}`} alt="Camera Feed" />
          ) : (
            <div className="camera-placeholder">
              <p>No camera feed available</p>
            </div>
          )}
        </div>

        <div className="joystick-container panel">
          <h2>Joystick Control</h2>
          <div ref={joystickRef} style={{ width: '200px', height: '200px' }}></div>
          <div className="joystick-info">
            <p>Drag to control robot movement</p>
          </div>
        </div>

        <div className="panel">
          <h2>Navigation</h2>
          <form onSubmit={handleSetGoal} className="goal-form">
            <div className="form-group">
              <label>Target X (m)</label>
              <input
                type="number"
                step="0.1"
                className="input"
                value={goalX}
                onChange={(e) => setGoalX(parseFloat(e.target.value))}
              />
            </div>
            <div className="form-group">
              <label>Target Y (m)</label>
              <input
                type="number"
                step="0.1"
                className="input"
                value={goalY}
                onChange={(e) => setGoalY(parseFloat(e.target.value))}
              />
            </div>
            <div className="form-group">
              <label>Orientation (°)</label>
              <input
                type="number"
                step="1"
                className="input"
                value={goalOrientation}
                onChange={(e) => setGoalOrientation(parseFloat(e.target.value))}
              />
            </div>
            <div className="button-group">
              <button type="submit" className="btn btn-primary" disabled={isNavigating}>
                Set Goal
              </button>
              <button
                type="button"
                onClick={handleCancelGoal}
                className="btn btn-danger"
                disabled={!isNavigating}
              >
                Cancel
              </button>
            </div>
          </form>
          {isNavigating && (
            <div className="navigating-status">
              <span className="pulse-dot"></span>
              <span>Navigating to goal...</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default RobotControlView
