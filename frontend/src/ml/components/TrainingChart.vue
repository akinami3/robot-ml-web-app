<template>
  <div class="training-chart">
    <h3>学習曲線</h3>
    <svg v-if="metrics.length" width="400" height="200">
      <polyline
        :points="polylinePoints"
        fill="none"
        stroke="#2563eb"
        stroke-width="2"
      />
    </svg>
    <p v-else>メトリクスはまだありません。</p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface TrainingMetric {
  epoch: number
  metric_value: number
}

const props = defineProps<{ metrics: TrainingMetric[] }>()

const polylinePoints = computed(() => {
  if (!props.metrics.length) return ''
  const maxEpoch = Math.max(...props.metrics.map((m) => m.epoch)) || 1
  const maxValue = Math.max(...props.metrics.map((m) => m.metric_value)) || 1
  return props.metrics
    .map((metric) => {
      const x = (metric.epoch / maxEpoch) * 380 + 10
      const y = 190 - (metric.metric_value / maxValue) * 180
      return `${x},${y}`
    })
    .join(' ')
})
</script>

<style scoped>
.training-chart {
  background: #fff;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}
</style>
