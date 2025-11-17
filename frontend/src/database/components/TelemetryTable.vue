<template>
  <table class="telemetry-table">
    <thead>
      <tr>
        <th>セッションID</th>
        <th>名前</th>
        <th>状態</th>
        <th>記録</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="session in sessions" :key="session.id">
        <td>{{ session.id }}</td>
        <td>{{ session.name }}</td>
        <td>{{ session.status }}</td>
        <td>
          <span>速度: {{ session.capture_velocity ? 'ON' : 'OFF' }}</span>
          <span>状態: {{ session.capture_state ? 'ON' : 'OFF' }}</span>
          <span>画像: {{ session.capture_images ? 'ON' : 'OFF' }}</span>
        </td>
      </tr>
    </tbody>
  </table>
</template>

<script setup lang="ts">
interface TelemetrySession {
  id: string
  name: string
  status: string
  capture_velocity: boolean
  capture_state: boolean
  capture_images: boolean
}

interface Props {
  sessions: TelemetrySession[]
}

defineProps<Props>()
</script>

<style scoped>
.telemetry-table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

th,
td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #e5e7eb;
}

th {
  text-align: left;
  background: #f3f4f6;
}

td span {
  display: block;
}
</style>
