/**
 * ML Training Composable
 * 
 * Manages machine learning model training and monitoring
 */
import { ref, onMounted } from 'vue'
import { useWebSocket } from './useWebSocket'
import api from '@/services/api'

export interface MLModel {
  id: string
  name: string
  model_type: string
  architecture?: string
  status: string
  created_at: string
  last_trained_at?: string
}

export interface TrainingMetrics {
  epoch: number
  train_loss: number
  val_loss?: number
  train_accuracy?: number
  val_accuracy?: number
  learning_rate?: number
}

export interface TrainingConfig {
  dataset_id: string
  epochs: number
  batch_size?: number
  learning_rate?: number
  device?: string
  early_stopping_patience?: number
}

export function useMLTraining() {
  const models = ref<MLModel[]>([])
  const currentModel = ref<MLModel | null>(null)
  const trainingMetrics = ref<TrainingMetrics[]>([])
  const isTraining = ref(false)
  const currentEpoch = ref(0)
  const totalEpochs = ref(0)

  // WebSocket for real-time training metrics
  const { isConnected } = useWebSocket(
    `${import.meta.env.VITE_WS_URL || 'ws://localhost:8000'}/api/v1/ws/ml`,
    {
      onMessage: (message) => {
        if (message.type === 'training_progress') {
          const { epoch, train_loss, val_loss } = message.data
          currentEpoch.value = epoch

          trainingMetrics.value.push({
            epoch,
            train_loss,
            val_loss,
            timestamp: new Date().toISOString(),
          } as any)

          // Keep only last 100 metrics
          if (trainingMetrics.value.length > 100) {
            trainingMetrics.value = trainingMetrics.value.slice(-100)
          }
        } else if (message.type === 'training_complete') {
          isTraining.value = false
          fetchModels()
        } else if (message.type === 'training_error') {
          isTraining.value = false
          console.error('Training error:', message.data.error)
        }
      },
    }
  )

  // Fetch all models
  const fetchModels = async () => {
    try {
      const response = await api.get('/api/v1/ml/models')
      models.value = response.data
    } catch (error) {
      console.error('Failed to fetch models:', error)
    }
  }

  // Create new model
  const createModel = async (modelData: {
    name: string
    model_type: string
    architecture?: string
    dataset_id?: string
  }) => {
    try {
      const response = await api.post('/api/v1/ml/models', modelData)
      await fetchModels()
      return response.data
    } catch (error) {
      console.error('Failed to create model:', error)
      throw error
    }
  }

  // Delete model
  const deleteModel = async (modelId: string) => {
    try {
      await api.delete(`/api/v1/ml/models/${modelId}`)
      await fetchModels()
    } catch (error) {
      console.error('Failed to delete model:', error)
      throw error
    }
  }

  // Start training
  const startTraining = async (modelId: string, config: TrainingConfig) => {
    try {
      await api.post('/api/v1/ml/training/start', {
        model_id: modelId,
        config,
      })
      isTraining.value = true
      totalEpochs.value = config.epochs
      currentEpoch.value = 0
      trainingMetrics.value = []
    } catch (error) {
      console.error('Failed to start training:', error)
      throw error
    }
  }

  // Stop training
  const stopTraining = async (modelId: string) => {
    try {
      await api.post('/api/v1/ml/training/stop', {
        model_id: modelId,
      })
      isTraining.value = false
    } catch (error) {
      console.error('Failed to stop training:', error)
      throw error
    }
  }

  // Get model details
  const fetchModel = async (modelId: string) => {
    try {
      const response = await api.get(`/api/v1/ml/models/${modelId}`)
      currentModel.value = response.data
      return response.data
    } catch (error) {
      console.error('Failed to fetch model:', error)
      throw error
    }
  }

  onMounted(() => {
    fetchModels()
  })

  return {
    models,
    currentModel,
    trainingMetrics,
    isTraining,
    currentEpoch,
    totalEpochs,
    isConnected,
    fetchModels,
    createModel,
    deleteModel,
    startTraining,
    stopTraining,
    fetchModel,
  }
}
