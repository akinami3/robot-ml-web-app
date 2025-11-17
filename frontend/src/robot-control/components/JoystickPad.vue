<template>
  <div class="joystick" @pointerdown.prevent="start" @pointermove.prevent="move" @pointerup="end" @pointerleave="end">
    <div class="joystick-knob" :style="knobStyle"></div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive } from 'vue'

const emit = defineEmits<{
  update: [{ vx: number; vy: number; omega: number }]
}>()

const state = reactive({
  active: false,
  x: 0,
  y: 0,
})

const knobStyle = computed(() => ({
  transform: `translate(${state.x}px, ${state.y}px)`,
}))

const start = () => {
  state.active = true
}

const move = (event: PointerEvent) => {
  if (!state.active) return
  const rect = (event.currentTarget as HTMLElement).getBoundingClientRect()
  const centerX = rect.width / 2
  const centerY = rect.height / 2
  const offsetX = event.clientX - rect.left - centerX
  const offsetY = event.clientY - rect.top - centerY
  state.x = Math.max(-centerX, Math.min(centerX, offsetX))
  state.y = Math.max(-centerY, Math.min(centerY, offsetY))
  emit('update', {
    vx: state.y / centerY,
    vy: state.x / centerX,
    omega: -state.x / centerX,
  })
}

const end = () => {
  state.active = false
  state.x = 0
  state.y = 0
  emit('update', { vx: 0, vy: 0, omega: 0 })
}
</script>

<style scoped>
.joystick {
  width: 200px;
  height: 200px;
  border-radius: 50%;
  background: radial-gradient(circle, #d1d5db, #9ca3af);
  position: relative;
  touch-action: none;
}

.joystick-knob {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: #1f2937;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  transition: transform 0.05s ease;
}
</style>
