<template>
  <div id="app">
    <Header />
    <main class="main-content">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { RouterView } from 'vue-router'
import Header from './components/layout/Header.vue'
import { onMounted, onUnmounted } from 'vue'
import { useConnectionStore } from './store/connection'

const connectionStore = useConnectionStore()

onMounted(() => {
  connectionStore.startMonitoring()
})

onUnmounted(() => {
  connectionStore.stopMonitoring()
})
</script>

<style scoped>
#app {
  width: 100%;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  overflow: auto;
}
</style>
