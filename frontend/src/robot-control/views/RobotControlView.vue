<template>
  <section class="robot-control">
    <h2>ロボット制御</h2>
    <div class="control-panels">
      <JoystickPad @update="handleJoystick" />
      <div class="status-panel">
        <h3>状態</h3>
        <pre>{{ JSON.stringify(robotState, null, 2) }}</pre>
      </div>
      <div class="camera-panel">
        <h3>カメラ</h3>
        <img v-if="cameraStreamUrl" :src="cameraStreamUrl" alt="robot camera" />
        <p v-else>映像はまだ受信していません。</p>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import JoystickPad from '../components/JoystickPad.vue'
import { useRobotControl } from '../composables/useRobotControl'

const { robotState, cameraStreamUrl, sendVelocityCommand } = useRobotControl()

const handleJoystick = (payload: { vx: number; vy: number; omega: number }) => {
  sendVelocityCommand(payload)
}
</script>

<style scoped>
.robot-control {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.control-panels {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1.5rem;
}

.status-panel,
.camera-panel {
  background: #fff;
  border-radius: 8px;
  padding: 1rem;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.camera-panel img {
  width: 100%;
  border-radius: 8px;
}
</style>
