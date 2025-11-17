<template>
  <form class="training-config" @submit.prevent="handleSubmit">
    <label>
      ジョブ名
      <input v-model="form.name" type="text" required />
    </label>
    <label>
      エポック数
      <input v-model.number="form.epochs" type="number" min="1" />
    </label>
    <label>
      学習率
      <input v-model.number="form.learningRate" type="number" step="0.0001" min="0" />
    </label>
    <label>
      使用セッションID (カンマ区切り)
      <input v-model="form.datasetSessionIds" type="text" />
    </label>
    <button type="submit">ジョブ作成</button>
  </form>
</template>

<script setup lang="ts">
import { reactive } from 'vue'

const emit = defineEmits<{
  submit: [payload: Record<string, any>]
}>()

const form = reactive({
  name: 'ML Job',
  epochs: 3,
  learningRate: 0.001,
  datasetSessionIds: '',
})

const handleSubmit = () => {
  const sessionIds = form.datasetSessionIds
    .split(',')
    .map((id) => id.trim())
    .filter(Boolean)
  emit('submit', {
    name: form.name,
    config: {
      epochs: form.epochs,
      learning_rate: form.learningRate,
    },
    dataset_session_ids: sessionIds,
  })
}
</script>

<style scoped>
.training-config {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  background: #fff;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

button {
  align-self: flex-start;
  padding: 0.5rem 1.5rem;
  border: none;
  border-radius: 4px;
  background: #2563eb;
  color: #fff;
  cursor: pointer;
}
</style>
