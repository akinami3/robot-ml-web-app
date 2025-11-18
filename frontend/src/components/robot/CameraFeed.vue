<template>
  <div class="camera-feed">
    <div class="camera-header">
      <h3>Camera Feed</h3>
      <div class="status-indicator" :class="{ active: isConnected }">
        <span class="dot"></span>
        <span>{{ isConnected ? 'Live' : 'Disconnected' }}</span>
      </div>
    </div>
    <div class="camera-view">
      <img
        v-if="cameraImage"
        :src="cameraImage"
        alt="Robot camera feed"
        class="camera-image"
      />
      <div v-else class="no-feed">
        <svg
          class="camera-icon"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
          />
        </svg>
        <p>No camera feed available</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  cameraImage: string
  isConnected: boolean
}>()
</script>

<style scoped>
.camera-feed {
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.camera-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.camera-header h3 {
  margin: 0;
  font-size: 1.125rem;
  color: #1f2937;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: #6b7280;
}

.status-indicator.active {
  color: #10b981;
}

.status-indicator .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #6b7280;
}

.status-indicator.active .dot {
  background: #10b981;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.camera-view {
  aspect-ratio: 16 / 9;
  background: #111827;
  display: flex;
  align-items: center;
  justify-content: center;
}

.camera-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.no-feed {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #6b7280;
  padding: 2rem;
}

.camera-icon {
  width: 64px;
  height: 64px;
  margin-bottom: 1rem;
}

.no-feed p {
  margin: 0;
  font-size: 0.875rem;
}
</style>
