<template>
  <section class="ml-view">
    <h2>機械学習</h2>
    <div class="layout">
      <TrainingConfigForm @submit="handleSubmit" />
      <TrainingChart :metrics="metrics" />
    </div>
    <div class="jobs">
      <h3>ジョブ一覧</h3>
      <ul>
        <li v-for="job in jobs" :key="job.id">
          {{ job.name }} - {{ job.status }}
        </li>
      </ul>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'

import TrainingChart from '../components/TrainingChart.vue'
import TrainingConfigForm from '../components/TrainingConfigForm.vue'
import { useTrainingDashboard } from '../composables/useTrainingDashboard'

const { jobs, metrics, fetchJobs, createJob } = useTrainingDashboard()

onMounted(() => {
  fetchJobs()
})

const handleSubmit = async (config: Record<string, any>) => {
  await createJob(config)
}
</script>

<style scoped>
.ml-view {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.layout {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
}

.jobs {
  background: #fff;
  padding: 1rem;
  border-radius: 8px;
}
</style>
