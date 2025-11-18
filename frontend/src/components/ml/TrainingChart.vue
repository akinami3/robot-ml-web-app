<template>
  <div class="training-chart">
    <div class="chart-header">
      <h3>Training Progress</h3>
      <div v-if="isTraining" class="training-status">
        <span class="pulse-dot"></span>
        <span>Training... ({{ currentEpoch }}/{{ totalEpochs }})</span>
      </div>
    </div>
    <div class="chart-container">
      <canvas ref="chartCanvas"></canvas>
    </div>
    <div v-if="latestMetrics" class="metrics-summary">
      <div class="metric-item">
        <span class="metric-label">Train Loss</span>
        <span class="metric-value">{{ latestMetrics.train_loss?.toFixed(4) || 'N/A' }}</span>
      </div>
      <div class="metric-item">
        <span class="metric-label">Val Loss</span>
        <span class="metric-value">{{ latestMetrics.val_loss?.toFixed(4) || 'N/A' }}</span>
      </div>
      <div class="metric-item">
        <span class="metric-label">Learning Rate</span>
        <span class="metric-value">{{ latestMetrics.learning_rate?.toFixed(6) || 'N/A' }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, computed } from 'vue'
import {
  Chart,
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'

// Register Chart.js components
Chart.register(
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Title,
  Tooltip,
  Legend
)

interface TrainingMetrics {
  epoch: number
  train_loss: number
  val_loss?: number
  train_accuracy?: number
  val_accuracy?: number
  learning_rate?: number
}

const props = defineProps<{
  metrics: TrainingMetrics[]
  isTraining: boolean
  currentEpoch: number
  totalEpochs: number
}>()

const chartCanvas = ref<HTMLCanvasElement | null>(null)
let chartInstance: Chart | null = null

const latestMetrics = computed(() => {
  return props.metrics[props.metrics.length - 1]
})

const initChart = () => {
  if (!chartCanvas.value) return

  const ctx = chartCanvas.value.getContext('2d')
  if (!ctx) return

  chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [
        {
          label: 'Train Loss',
          data: [],
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          tension: 0.4,
        },
        {
          label: 'Val Loss',
          data: [],
          borderColor: '#10b981',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          tension: 0.4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          position: 'top',
        },
        tooltip: {
          mode: 'index',
          intersect: false,
        },
      },
      scales: {
        x: {
          title: {
            display: true,
            text: 'Epoch',
          },
        },
        y: {
          title: {
            display: true,
            text: 'Loss',
          },
          beginAtZero: true,
        },
      },
    },
  })
}

const updateChart = () => {
  if (!chartInstance) return

  const epochs = props.metrics.map((m) => m.epoch.toString())
  const trainLoss = props.metrics.map((m) => m.train_loss)
  const valLoss = props.metrics.map((m) => m.val_loss || null)

  chartInstance.data.labels = epochs
  chartInstance.data.datasets[0].data = trainLoss
  chartInstance.data.datasets[1].data = valLoss

  chartInstance.update('none') // Update without animation for real-time
}

watch(
  () => props.metrics,
  () => {
    updateChart()
  },
  { deep: true }
)

onMounted(() => {
  initChart()
  updateChart()
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.destroy()
  }
})
</script>

<style scoped>
.training-chart {
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: 1.5rem;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.chart-header h3 {
  margin: 0;
  font-size: 1.125rem;
  color: #1f2937;
}

.training-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: #3b82f6;
  font-weight: 500;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #3b82f6;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.3;
  }
}

.chart-container {
  height: 300px;
  margin-bottom: 1rem;
}

.metrics-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
}

.metric-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.metric-label {
  font-size: 0.75rem;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.metric-value {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
  font-family: monospace;
}
</style>
