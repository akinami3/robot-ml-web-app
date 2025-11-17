import { ref } from 'vue'

import { mlApi } from '../../shared/services/apiClient'
import { websocketManager } from '../../shared/services/wsClient'

interface TrainingJob {
  id: string
  name: string
  status: string
}

interface TrainingMetric {
  epoch: number
  metric_value: number
}

export function useTrainingDashboard() {
  const jobs = ref<TrainingJob[]>([])
  const metrics = ref<TrainingMetric[]>([])
  let unsubscribe: (() => void) | null = null

  const fetchJobs = async () => {
    jobs.value = await mlApi.listJobs()
  }

  const createJob = async (config: Record<string, any>) => {
    const payload = {
      name: config.name,
      dataset_session_ids: config.dataset_session_ids,
      config: config.config,
    }
    await mlApi.createJob(payload)
    await fetchJobs()
  }

  const subscribeMetrics = () => {
    if (unsubscribe) return
    unsubscribe = websocketManager.subscribe('training', (message: any) => {
      if (message.metric_name === 'loss') {
        metrics.value.push({
          epoch: message.epoch,
          metric_value: message.metric_value,
        })
      }
    })
  }

  subscribeMetrics()

  return {
    jobs,
    metrics,
    fetchJobs,
    createJob,
  }
}
