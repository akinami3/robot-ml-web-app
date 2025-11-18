<template>
  <div class="recording-controls">
    <div class="control-header">
      <h3>Recording Controls</h3>
      <div v-if="currentSession" class="session-info">
        <span class="session-name">{{ currentSession.name }}</span>
        <span class="data-count">{{ currentSession.data_point_count || 0 }} data points</span>
      </div>
    </div>

    <!-- Start Recording Form -->
    <div v-if="!currentSession" class="start-form">
      <input
        v-model="newSessionName"
        type="text"
        placeholder="Session name"
        class="input"
      />
      <textarea
        v-model="newSessionDescription"
        placeholder="Description (optional)"
        rows="2"
        class="input"
      ></textarea>
      <button
        @click="handleStart"
        class="btn btn-primary"
        :disabled="!newSessionName.trim()"
      >
        <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122"
          />
        </svg>
        Start Recording
      </button>
    </div>

    <!-- Active Session Controls -->
    <div v-else class="active-controls">
      <div class="status-badge" :class="statusClass">
        <span class="status-dot"></span>
        {{ currentSession.status.toUpperCase() }}
      </div>

      <div class="button-group">
        <!-- Pause/Resume -->
        <button
          v-if="isRecording"
          @click="$emit('pause')"
          class="btn btn-warning"
        >
          <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          Pause
        </button>

        <button
          v-if="isPaused"
          @click="$emit('resume')"
          class="btn btn-success"
        >
          <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
            />
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          Resume
        </button>

        <!-- Save -->
        <button @click="$emit('save')" class="btn btn-success">
          <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M5 13l4 4L19 7"
            />
          </svg>
          Save
        </button>

        <!-- Discard -->
        <button @click="handleDiscard" class="btn btn-danger">
          <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
            />
          </svg>
          Discard
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface RecordingSession {
  id: string
  name: string
  description?: string
  status: 'recording' | 'paused' | 'completed' | 'discarded'
  data_point_count?: number
}

const props = defineProps<{
  currentSession: RecordingSession | null
}>()

const emit = defineEmits<{
  start: [name: string, description: string]
  pause: []
  resume: []
  save: []
  discard: []
}>()

const newSessionName = ref('')
const newSessionDescription = ref('')

const isRecording = computed(() => props.currentSession?.status === 'recording')
const isPaused = computed(() => props.currentSession?.status === 'paused')

const statusClass = computed(() => {
  if (isRecording.value) return 'status-recording'
  if (isPaused.value) return 'status-paused'
  return ''
})

const handleStart = () => {
  emit('start', newSessionName.value, newSessionDescription.value)
  newSessionName.value = ''
  newSessionDescription.value = ''
}

const handleDiscard = () => {
  if (confirm('Are you sure you want to discard this recording?')) {
    emit('discard')
  }
}
</script>

<style scoped>
.recording-controls {
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: 1.5rem;
}

.control-header {
  margin-bottom: 1.5rem;
}

.control-header h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.125rem;
  color: #1f2937;
}

.session-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.875rem;
}

.session-name {
  font-weight: 600;
  color: #1f2937;
}

.data-count {
  color: #6b7280;
}

.start-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.input {
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  transition: border-color 0.2s;
}

.input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
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

.btn-success {
  background: #10b981;
  color: white;
}

.btn-success:hover:not(:disabled) {
  background: #059669;
}

.btn-warning {
  background: #f59e0b;
  color: white;
}

.btn-warning:hover:not(:disabled) {
  background: #d97706;
}

.btn-danger {
  background: #ef4444;
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background: #dc2626;
}

.icon {
  width: 1.25rem;
  height: 1.25rem;
}

.active-controls {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  width: fit-content;
}

.status-recording {
  background: #fee2e2;
  color: #991b1b;
}

.status-paused {
  background: #fef3c7;
  color: #92400e;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
}

.status-recording .status-dot {
  animation: pulse 1.5s infinite;
}

.button-group {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}
</style>
