import { useState, useEffect, useRef } from 'react'
import { config as appConfig } from '../config'
import api from '../services/api'
import { Chart, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js'
import { Line } from 'react-chartjs-2'
import './Views.css'

// Register Chart.js components
Chart.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend)

const MLView = () => {
  const [isTraining, setIsTraining] = useState(false)
  const [trainingData, setTrainingData] = useState({
    epochs: [] as number[],
    trainLoss: [] as number[],
    valLoss: [] as number[],
  })
  const [mlConfig, setMlConfig] = useState({
    dataset: 'dataset1',
    modelType: 'cnn',
    batchSize: 32,
    epochs: 10,
    learningRate: 0.001,
    optimizer: 'adam',
  })
  
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    if (isTraining && !wsRef.current) {
      const wsUrl = `${appConfig.wsUrl}/api/v1/ws/ml`
      const ws = new WebSocket(wsUrl)

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        if (data.type === 'training_progress') {
          setTrainingData(prev => ({
            epochs: [...prev.epochs, data.data.epoch],
            trainLoss: [...prev.trainLoss, data.data.train_loss],
            valLoss: [...prev.valLoss, data.data.val_loss],
          }))
        } else if (data.type === 'training_complete') {
          setIsTraining(false)
          alert('Training completed successfully!')
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
  }, [isTraining])

  const handleStartTraining = async () => {
    try {
      await api.post('/api/v1/ml/training/start', {
        dataset: mlConfig.dataset,
        model_type: mlConfig.modelType,
        batch_size: mlConfig.batchSize,
        epochs: mlConfig.epochs,
        learning_rate: mlConfig.learningRate,
        optimizer: mlConfig.optimizer,
      })
      setIsTraining(true)
      setTrainingData({ epochs: [], trainLoss: [], valLoss: [] })
    } catch (error) {
      console.error('Failed to start training:', error)
      alert('Failed to start training')
    }
  }

  const handleStopTraining = async () => {
    try {
      await api.post('/api/v1/ml/training/stop')
      setIsTraining(false)
    } catch (error) {
      console.error('Failed to stop training:', error)
    }
  }

  const chartData = {
    labels: trainingData.epochs,
    datasets: [
      {
        label: 'Training Loss',
        data: trainingData.trainLoss,
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
      },
      {
        label: 'Validation Loss',
        data: trainingData.valLoss,
        borderColor: '#ef4444',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        tension: 0.4,
      },
    ],
  }

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Training & Validation Loss',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Loss',
        },
      },
      x: {
        title: {
          display: true,
          text: 'Epoch',
        },
      },
    },
  }

  return (
    <div className="view ml-view">
      <div className="view-header">
        <h1>Machine Learning</h1>
        <p className="subtitle">Train and evaluate ML models</p>
      </div>

      <div className="panel">
        <h2>Training Configuration</h2>
        
        <div className="training-form">
          <div className="form-group">
            <label>Dataset</label>
            <select
              className="input"
              value={mlConfig.dataset}
              onChange={(e) => setMlConfig({...mlConfig, dataset: e.target.value})}
              disabled={isTraining}
            >
              <option value="dataset1">Dataset 1</option>
              <option value="dataset2">Dataset 2</option>
            </select>
          </div>

          <div className="form-group">
            <label>Model Type</label>
            <select
              className="input"
              value={mlConfig.modelType}
              onChange={(e) => setMlConfig({...mlConfig, modelType: e.target.value})}
              disabled={isTraining}
            >
              <option value="cnn">CNN</option>
              <option value="resnet">ResNet</option>
              <option value="mobilenet">MobileNet</option>
            </select>
          </div>

          <div className="form-group">
            <label>Batch Size</label>
            <input
              type="number"
              className="input"
              value={mlConfig.batchSize}
              onChange={(e) => setMlConfig({...mlConfig, batchSize: parseInt(e.target.value)})}
              disabled={isTraining}
              min="1"
            />
          </div>

          <div className="form-group">
            <label>Epochs</label>
            <input
              type="number"
              className="input"
              value={mlConfig.epochs}
              onChange={(e) => setMlConfig({...mlConfig, epochs: parseInt(e.target.value)})}
              disabled={isTraining}
              min="1"
            />
          </div>

          <div className="form-group">
            <label>Learning Rate</label>
            <input
              type="number"
              className="input"
              value={mlConfig.learningRate}
              onChange={(e) => setMlConfig({...mlConfig, learningRate: parseFloat(e.target.value)})}
              disabled={isTraining}
              step="0.0001"
            />
          </div>

          <div className="form-group">
            <label>Optimizer</label>
            <select
              className="input"
              value={mlConfig.optimizer}
              onChange={(e) => setMlConfig({...mlConfig, optimizer: e.target.value})}
              disabled={isTraining}
            >
              <option value="adam">Adam</option>
              <option value="sgd">SGD</option>
              <option value="rmsprop">RMSprop</option>
            </select>
          </div>
        </div>

        <div className="button-group" style={{ marginTop: '1.5rem' }}>
          <button onClick={handleStartTraining} className="btn btn-primary" disabled={isTraining}>
            トレーニング開始
          </button>
          <button onClick={handleStopTraining} className="btn btn-danger" disabled={!isTraining}>
            トレーニング停止
          </button>
        </div>

        {isTraining && (
          <div className="navigating-status" style={{ marginTop: '1rem' }}>
            <span className="pulse-dot"></span>
            <span>Training in progress...</span>
          </div>
        )}
      </div>

      <div className="panel">
        <h2>Training Progress</h2>
        <div className="chart-container">
          <Line data={chartData} options={chartOptions} />
        </div>
      </div>
    </div>
  )
}

export default MLView
