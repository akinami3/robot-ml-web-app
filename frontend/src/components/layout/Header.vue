<template>
  <header class="header">
    <div class="header-content">
      <h1 class="title">Robot ML Web App</h1>
      
      <nav class="nav">
        <RouterLink to="/robot-control" class="nav-link">ロボット制御</RouterLink>
        <RouterLink to="/database" class="nav-link">データベース</RouterLink>
        <RouterLink to="/machine-learning" class="nav-link">機械学習</RouterLink>
        <RouterLink to="/chatbot" class="nav-link">チャットボット</RouterLink>
      </nav>

      <div class="header-actions">
        <button @click="startSimulator" class="btn btn-primary" :disabled="simulatorRunning">
          シミュレーション起動
        </button>
        <button @click="stopSimulator" class="btn btn-danger" :disabled="!simulatorRunning">
          シミュレーション終了
        </button>

        <div class="status-indicators">
          <div class="status-item" :class="{ connected: connectionStore.mqttConnected }">
            <span class="status-dot"></span>
            <span class="status-label">MQTT</span>
          </div>
          <div class="status-item" :class="{ connected: connectionStore.websocketConnected }">
            <span class="status-dot"></span>
            <span class="status-label">WS</span>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import { useConnectionStore } from '@/store/connection'
import api from '@/services/api'

const connectionStore = useConnectionStore()
const simulatorRunning = ref(false)

async function startSimulator() {
  try {
    await api.post('/api/v1/robot/simulator/start')
    simulatorRunning.value = true
  } catch (error) {
    console.error('Failed to start simulator:', error)
    alert('シミュレータの起動に失敗しました')
  }
}

async function stopSimulator() {
  try {
    await api.post('/api/v1/robot/simulator/stop')
    simulatorRunning.value = false
  } catch (error) {
    console.error('Failed to stop simulator:', error)
    alert('シミュレータの停止に失敗しました')
  }
}
</script>

<style scoped>
.header {
  background: white;
  border-bottom: 1px solid var(--border-color);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 1rem 2rem;
  display: flex;
  align-items: center;
  gap: 2rem;
}

.title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--primary-color);
}

.nav {
  flex: 1;
  display: flex;
  gap: 1rem;
}

.nav-link {
  padding: 0.5rem 1rem;
  text-decoration: none;
  color: var(--text-secondary);
  border-radius: 4px;
  transition: all 0.2s;
}

.nav-link:hover {
  background: #f3f4f6;
  color: var(--text-primary);
}

.nav-link.router-link-active {
  background: var(--primary-color);
  color: white;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--primary-color);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-danger {
  background: var(--danger-color);
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background: #dc2626;
}

.status-indicators {
  display: flex;
  gap: 0.75rem;
  padding-left: 1rem;
  border-left: 1px solid var(--border-color);
}

.status-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--danger-color);
  transition: background 0.3s;
}

.status-item.connected .status-dot {
  background: var(--success-color);
}

.status-label {
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--text-secondary);
}
</style>
