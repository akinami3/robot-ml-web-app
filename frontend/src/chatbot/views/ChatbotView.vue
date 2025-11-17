<template>
  <section class="chatbot-view">
    <h2>Chatbot</h2>
    <ConversationPanel :messages="messages" @submit="handleSubmit" />
  </section>
</template>

<script setup lang="ts">
import ConversationPanel from '../components/ConversationPanel.vue'
import { useChatbot } from '../composables/useChatbot'

const { messages, ask } = useChatbot()

const handleSubmit = async (question: string) => {
  await ask(question)
}
</script>

<style scoped>
.chatbot-view {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}
</style>
