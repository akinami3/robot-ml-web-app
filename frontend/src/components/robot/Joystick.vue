<template>
  <div class="joystick-container">
    <div class="joystick-title">
      <h3>Joystick Control</h3>
      <p class="help-text">Touch and drag to control the robot</p>
    </div>
    <div ref="joystickZone" class="joystick-zone"></div>
    <div class="joystick-info">
      <div class="info-item">
        <span class="label">Linear X:</span>
        <span class="value">{{ joystickData.vx.toFixed(2) }}</span>
      </div>
      <div class="info-item">
        <span class="label">Linear Y:</span>
        <span class="value">{{ joystickData.vy.toFixed(2) }}</span>
      </div>
      <div class="info-item">
        <span class="label">Angular:</span>
        <span class="value">{{ joystickData.angular.toFixed(2) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useJoystick } from '@/composables/useJoystick'

const props = defineProps<{
  onMove?: (data: any) => void
  onEnd?: () => void
  maxSpeed?: number
  maxAngular?: number
}>()

const joystickZone = ref<HTMLElement | null>(null)

const { joystickData } = useJoystick(joystickZone, {
  maxSpeed: props.maxSpeed || 1.0,
  maxAngular: props.maxAngular || 1.0,
  onMove: (data) => {
    props.onMove?.(data)
  },
  onEnd: () => {
    props.onEnd?.()
  },
})
</script>

<style scoped>
.joystick-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1.5rem;
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.joystick-title {
  text-align: center;
  margin-bottom: 1rem;
}

.joystick-title h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.25rem;
  color: #1f2937;
}

.help-text {
  margin: 0;
  font-size: 0.875rem;
  color: #6b7280;
}

.joystick-zone {
  width: 300px;
  height: 300px;
  position: relative;
  background: #f3f4f6;
  border-radius: 50%;
  margin: 1rem 0;
}

.joystick-info {
  display: flex;
  gap: 1.5rem;
  margin-top: 1rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.info-item .label {
  font-size: 0.75rem;
  color: #6b7280;
  margin-bottom: 0.25rem;
}

.info-item .value {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
  font-family: monospace;
}
</style>
