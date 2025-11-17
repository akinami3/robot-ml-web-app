<template>
  <div class="connection-icon" :class="{ online: connected }" :title="label">
    <span class="indicator"></span>
    <span class="label">{{ label }}</span>
  </div>
</template>

<script setup lang="ts">
interface Props {
  label: string
  connected: boolean
}

const props = defineProps<Props>()
</script>

<style scoped>
.connection-icon {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.2rem 0.5rem;
  border-radius: 999px;
  background: #374151;
  color: #f3f4f6;
  font-size: 0.9rem;
}

.connection-icon.online {
  background: #065f46;
}

.indicator {
  width: 0.6rem;
  height: 0.6rem;
  border-radius: 50%;
  background: #ef4444;
}

.connection-icon.online .indicator {
  background: #34d399;
}
</style>
