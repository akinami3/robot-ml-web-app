<template>
  <div class="app-shell">
    <header class="app-header">
      <h1>Robot ML Web App</h1>
      <div class="header-actions">
        <button @click="handleSimulationStart">シミュレーション起動</button>
        <button @click="handleSimulationStop">シミュレーション停止</button>
        <ConnectionIcon label="MQTT" :connected="connectionStatus.mqtt" />
        <ConnectionIcon label="WebSocket" :connected="connectionStatus.websocket" />
      </div>
    </header>
    <nav class="app-tabs">
      <RouterLink to="/robot-control">ロボット制御</RouterLink>
      <RouterLink to="/database">データベース画面</RouterLink>
      <RouterLink to="/ml">機械学習</RouterLink>
      <RouterLink to="/chatbot">Chatbot</RouterLink>
    </nav>
    <main class="app-main">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import ConnectionIcon from '../components/ConnectionIcon.vue'
import { useConnectionStore } from './store'
import { simulationApi } from '../shared/services/apiClient'

const connectionStore = useConnectionStore()
const connectionStatus = connectionStore.status

const handleSimulationStart = async () => {
  await simulationApi.start()
}

const handleSimulationStop = async () => {
  await simulationApi.stop()
}
</script>

<style scoped>
.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background: #1f2937;
  color: #fff;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.app-tabs {
  display: flex;
  gap: 1rem;
  padding: 0.75rem 2rem;
  background: #e5e7eb;
}

.app-main {
  flex: 1;
  padding: 2rem;
  background: #f9fafb;
}
</style>
