<template>
  <section class="database-view">
    <h2>データベース</h2>
    <RecordingControls
      @start="handleStart"
      @pause="handlePause"
      @save="handleSave"
      @discard="handleDiscard"
      @end="handleEnd"
    />
    <TelemetryTable :sessions="sessions" />
  </section>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'

import RecordingControls from '../components/RecordingControls.vue'
import TelemetryTable from '../components/TelemetryTable.vue'
import { useRecordingSession } from '../composables/useRecordingSession'

const {
  sessions,
  refreshSessions,
  startSession,
  pauseSession,
  saveSession,
  discardSession,
  endSession,
} = useRecordingSession()

onMounted(() => {
  refreshSessions()
})

const handleStart = async (payload: Record<string, any>) => {
  await startSession(payload)
}

const handlePause = async () => {
  await pauseSession()
}

const handleSave = async () => {
  await saveSession()
}

const handleDiscard = async () => {
  await discardSession()
}

const handleEnd = async (payload: { save: boolean }) => {
  await endSession(payload.save)
}
</script>

<style scoped>
.database-view {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}
</style>
