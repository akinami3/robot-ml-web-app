<template>
  <div class="database-view">
    <div class="view-header">
      <h1>Database & Recording</h1>
      <p class="subtitle">Record robot data and manage datasets</p>
    </div>

    <div class="database-grid">
      <!-- Recording Controls -->
      <RecordingControls
        :currentSession="currentSession"
        @start="handleStartRecording"
        @pause="handlePauseRecording"
        @resume="handleResumeRecording"
        @save="handleSaveRecording"
        @discard="handleDiscardRecording"
      />

      <!-- Sessions List -->
      <div class="sessions-panel">
        <div class="panel-header">
          <h2>Recording Sessions</h2>
          <button @click="fetchSessions" class="btn-refresh">
            <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            Refresh
          </button>
        </div>

        <div class="sessions-list">
          <div
            v-for="session in sessions"
            :key="session.id"
            class="session-card"
            :class="{ active: currentSession?.id === session.id }"
          >
            <div class="session-header">
              <h3>{{ session.name }}</h3>
              <span class="status-badge" :class="`status-${session.status}`">
                {{ session.status }}
              </span>
            </div>
            <div v-if="session.description" class="session-description">
              {{ session.description }}
            </div>
            <div class="session-meta">
              <span class="meta-item">
                <svg class="meta-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                  />
                </svg>
                {{ session.data_point_count || 0 }} points
              </span>
              <span class="meta-item">
                <svg class="meta-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                {{ formatDate(session.created_at) }}
              </span>
            </div>
          </div>

          <div v-if="sessions.length === 0" class="empty-state">
            <svg class="empty-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
              />
            </svg>
            <p>No recording sessions yet</p>
            <p class="empty-hint">Start a new recording to collect data</p>
          </div>
        </div>
      </div>

      <!-- Datasets Panel -->
      <div class="datasets-panel">
        <div class="panel-header">
          <h2>Datasets</h2>
          <button @click="showCreateDataset = true" class="btn-create">
            <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 4v16m8-8H4"
              />
            </svg>
            Create Dataset
          </button>
        </div>

        <div class="info-box">
          <svg class="info-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <p>
            Create datasets from completed recording sessions for machine learning training.
            Datasets will automatically split data into training, validation, and test sets.
          </p>
        </div>
      </div>
    </div>

    <!-- Create Dataset Modal (simplified) -->
    <div v-if="showCreateDataset" class="modal-overlay" @click="showCreateDataset = false">
      <div class="modal-content" @click.stop>
        <h2>Create Dataset</h2>
        <p class="modal-subtitle">Select completed sessions to create a dataset</p>
        <div class="modal-actions">
          <button @click="showCreateDataset = false" class="btn btn-secondary">
            Cancel
          </button>
          <button class="btn btn-primary">Create</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRecording } from '@/composables/useRecording'
import RecordingControls from '@/components/database/RecordingControls.vue'

const {
  sessions,
  currentSession,
  startRecording,
  pauseRecording,
  resumeRecording,
  saveRecording,
  discardRecording,
  fetchSessions,
} = useRecording()

const showCreateDataset = ref(false)

const handleStartRecording = async (name: string, description: string) => {
  try {
    await startRecording(name, description)
  } catch (error) {
    alert('Failed to start recording')
  }
}

const handlePauseRecording = async () => {
  try {
    await pauseRecording()
  } catch (error) {
    alert('Failed to pause recording')
  }
}

const handleResumeRecording = async () => {
  try {
    await resumeRecording()
  } catch (error) {
    alert('Failed to resume recording')
  }
}

const handleSaveRecording = async () => {
  try {
    await saveRecording()
  } catch (error) {
    alert('Failed to save recording')
  }
}

const handleDiscardRecording = async () => {
  try {
    await discardRecording()
  } catch (error) {
    alert('Failed to discard recording')
  }
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

onMounted(() => {
  fetchSessions()
})
</script>

<style scoped>
.database-view {
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

.database-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

@media (max-width: 1024px) {
  .database-grid {
    grid-template-columns: 1fr;
  }
}

.sessions-panel,
.datasets-panel {
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: 1.5rem;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.panel-header h2 {
  margin: 0;
  font-size: 1.125rem;
  color: #1f2937;
}

.btn-refresh,
.btn-create {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  background: white;
  color: #374151;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-refresh:hover,
.btn-create:hover {
  background: #f9fafb;
  border-color: #9ca3af;
}

.icon {
  width: 1.25rem;
  height: 1.25rem;
}

.sessions-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  max-height: 600px;
  overflow-y: auto;
}

.session-card {
  padding: 1rem;
  border: 2px solid #e5e7eb;
  border-radius: 0.5rem;
  transition: all 0.2s;
}

.session-card:hover {
  border-color: #d1d5db;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.session-card.active {
  border-color: #3b82f6;
  background: #eff6ff;
}

.session-header {
  display: flex;
  justify-content: space-between;
  align-items: start;
  margin-bottom: 0.5rem;
}

.session-header h3 {
  margin: 0;
  font-size: 1rem;
  color: #1f2937;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.status-recording {
  background: #fee2e2;
  color: #991b1b;
}

.status-paused {
  background: #fef3c7;
  color: #92400e;
}

.status-completed {
  background: #d1fae5;
  color: #065f46;
}

.status-discarded {
  background: #f3f4f6;
  color: #6b7280;
}

.session-description {
  font-size: 0.875rem;
  color: #6b7280;
  margin-bottom: 0.75rem;
}

.session-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.75rem;
  color: #9ca3af;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.meta-icon {
  width: 1rem;
  height: 1rem;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  text-align: center;
  color: #9ca3af;
}

.empty-icon {
  width: 64px;
  height: 64px;
  margin-bottom: 1rem;
}

.empty-state p {
  margin: 0.25rem 0;
}

.empty-hint {
  font-size: 0.875rem;
}

.info-box {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  background: #eff6ff;
  border-radius: 0.5rem;
  border: 1px solid #bfdbfe;
}

.info-icon {
  width: 1.5rem;
  height: 1.5rem;
  color: #3b82f6;
  flex-shrink: 0;
}

.info-box p {
  margin: 0;
  font-size: 0.875rem;
  color: #1e40af;
  line-height: 1.5;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
}

.modal-content {
  background: white;
  border-radius: 0.5rem;
  padding: 2rem;
  max-width: 500px;
  width: 90%;
  box-shadow: 0 20px 25px rgba(0, 0, 0, 0.15);
}

.modal-content h2 {
  margin: 0 0 0.5rem 0;
  font-size: 1.5rem;
  color: #1f2937;
}

.modal-subtitle {
  margin: 0 0 1.5rem 0;
  color: #6b7280;
  font-size: 0.875rem;
}

.modal-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
  margin-top: 1.5rem;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover {
  background: #2563eb;
}

.btn-secondary {
  background: #f3f4f6;
  color: #374151;
}

.btn-secondary:hover {
  background: #e5e7eb;
}
</style>
