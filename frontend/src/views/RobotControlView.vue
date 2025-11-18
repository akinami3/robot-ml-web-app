<template>
  <div class="robot-control-view">
    <div class="view-header">
      <h1>Robot Control</h1>
      <p class="subtitle">Control the robot and monitor its status in real-time</p>
    </div>

    <div class="control-grid">
      <!-- Robot Status Panel -->
      <div class="status-panel">
        <h2>Robot Status</h2>
        <div v-if="robotStatus" class="status-info">
          <div class="status-item">
            <span class="label">Position X:</span>
            <span class="value">{{ robotStatus.position_x.toFixed(2) }} m</span>
          </div>
          <div class="status-item">
            <span class="label">Position Y:</span>
            <span class="value">{{ robotStatus.position_y.toFixed(2) }} m</span>
          </div>
          <div class="status-item">
            <span class="label">Orientation:</span>
            <span class="value">{{ (robotStatus.orientation * 180 / Math.PI).toFixed(1) }}°</span>
          </div>
          <div class="status-item">
            <span class="label">Battery:</span>
            <span class="value" :style="{ color: batteryColor }">
              {{ robotStatus.battery_level }}%
            </span>
          </div>
          <div class="status-item">
            <span class="label">Moving:</span>
            <span class="value">{{ robotStatus.is_moving ? 'Yes' : 'No' }}</span>
          </div>
        </div>
        <div v-else class="no-status">
          <p>No robot status available</p>
        </div>
      </div>

      <!-- Camera Feed -->
      <CameraFeed :cameraImage="cameraImage" :isConnected="isConnected" />

      <!-- Joystick Control -->
      <Joystick
        :onMove="handleJoystickMove"
        :onEnd="handleJoystickEnd"
        :maxSpeed="1.0"
        :maxAngular="1.0"
      />

      <!-- Navigation Panel -->
      <div class="navigation-panel">
        <h2>Navigation</h2>
        <form @submit.prevent="handleSetGoal" class="goal-form">
          <div class="form-group">
            <label>Target X (m)</label>
            <input v-model.number="goalX" type="number" step="0.1" class="input" />
          </div>
          <div class="form-group">
            <label>Target Y (m)</label>
            <input v-model.number="goalY" type="number" step="0.1" class="input" />
          </div>
          <div class="form-group">
            <label>Orientation (°)</label>
            <input v-model.number="goalOrientation" type="number" step="1" class="input" />
          </div>
          <div class="button-group">
            <button type="submit" class="btn btn-primary" :disabled="isNavigating">
              Set Goal
            </button>
            <button
              type="button"
              @click="handleCancelGoal"
              class="btn btn-danger"
              :disabled="!isNavigating"
            >
              Cancel
            </button>
          </div>
        </form>
        <div v-if="isNavigating" class="navigating-status">
          <span class="pulse-dot"></span>
          <span>Navigating to goal...</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRobotControl } from '@/composables/useRobotControl'
import Joystick from '@/components/robot/Joystick.vue'
import CameraFeed from '@/components/robot/CameraFeed.vue'

const {
  robotStatus,
  cameraImage,
  isNavigating,
  isConnected,
  sendVelocityWs,
  setNavigationGoal,
  cancelNavigation,
  batteryColor,
} = useRobotControl()

const goalX = ref(0)
const goalY = ref(0)
const goalOrientation = ref(0)

const handleJoystickMove = (data: any) => {
  sendVelocityWs(data.vx, data.vy, data.vz, data.angular)
}

const handleJoystickEnd = () => {
  sendVelocityWs(0, 0, 0, 0)
}

const handleSetGoal = async () => {
  try {
    await setNavigationGoal({
      target_x: goalX.value,
      target_y: goalY.value,
      target_orientation: (goalOrientation.value * Math.PI) / 180,
    })
  } catch (error) {
    alert('Failed to set navigation goal')
  }
}

const handleCancelGoal = async () => {
  try {
    await cancelNavigation()
  } catch (error) {
    alert('Failed to cancel navigation')
  }
}
</script>

<style scoped>
.robot-control-view {
  padding: 2rem;
}

.view-header {
  margin-bottom: 2rem;
}

.view-header h1 {
  margin: 0 0 0.5rem 0;
  font-size: 2rem;
  color: #1f2937;
}

.subtitle {
  margin: 0;
  color: #6b7280;
  font-size: 1rem;
}

.control-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 1.5rem;
}

.status-panel,
.navigation-panel {
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: 1.5rem;
}

.status-panel h2,
.navigation-panel h2 {
  margin: 0 0 1rem 0;
  font-size: 1.125rem;
  color: #1f2937;
}

.status-info {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.status-item {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 0;
  border-bottom: 1px solid #f3f4f6;
}

.status-item:last-child {
  border-bottom: none;
}

.status-item .label {
  font-size: 0.875rem;
  color: #6b7280;
}

.status-item .value {
  font-size: 0.875rem;
  font-weight: 600;
  color: #1f2937;
}

.no-status {
  padding: 2rem;
  text-align: center;
  color: #9ca3af;
}

.goal-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.form-group label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.input {
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
}

.input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.button-group {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.btn {
  flex: 1;
  padding: 0.625rem 1rem;
  border: none;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-danger {
  background: #ef4444;
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background: #dc2626;
}

.navigating-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 1rem;
  padding: 0.75rem 1rem;
  background: #dbeafe;
  border-radius: 0.375rem;
  color: #1e40af;
  font-size: 0.875rem;
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
</style>
