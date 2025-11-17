<template>
  <div class="recording-controls">
    <label>
      セッション名
      <input v-model="form.name" type="text" placeholder="新しいセッション" />
    </label>
    <div class="checkboxes">
      <label><input v-model="form.capture_velocity" type="checkbox" />速度</label>
      <label><input v-model="form.capture_state" type="checkbox" />状態</label>
      <label><input v-model="form.capture_images" type="checkbox" />画像</label>
    </div>
    <div class="buttons">
      <button @click="emit('start', form)">開始</button>
      <button @click="emit('pause')">一時停止</button>
      <button @click="emit('save')">保存</button>
      <button @click="emit('discard')">破棄</button>
      <button @click="handleEnd">終了</button>
    </div>
    <div v-if="showEndOptions" class="end-options">
      <button @click="emit('end', { save: true })">保存して終了</button>
      <button @click="emit('end', { save: false })">保存せずに終了</button>
      <button @click="showEndOptions = false">キャンセル</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'

const emit = defineEmits<{
  start: [payload: Record<string, any>]
  pause: []
  save: []
  discard: []
  end: [payload: { save: boolean }]
}>()

const form = reactive({
  name: 'セッション',
  capture_velocity: true,
  capture_state: true,
  capture_images: false,
})

const showEndOptions = ref(false)

const handleEnd = () => {
  showEndOptions.value = true
}
</script>

<style scoped>
.recording-controls {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  background: #fff;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.checkboxes,
.buttons,
.end-options {
  display: flex;
  gap: 0.75rem;
}

button {
  padding: 0.5rem 1rem;
  border-radius: 4px;
  border: none;
  background: #2563eb;
  color: #fff;
  cursor: pointer;
}

button:hover {
  background: #1d4ed8;
}

.end-options {
  gap: 0.5rem;
}
</style>
