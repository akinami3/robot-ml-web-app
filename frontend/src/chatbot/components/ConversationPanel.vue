<template>
  <div class="conversation-panel">
    <div class="messages">
      <div v-for="message in messages" :key="message.id" class="message">
        <p class="question">Q: {{ message.question }}</p>
        <p class="answer">A: {{ message.answer }}</p>
      </div>
    </div>
    <form class="prompt" @submit.prevent="handleSubmit">
      <input v-model="question" type="text" placeholder="質問を入力" />
      <button type="submit">送信</button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Message {
  id: string
  question: string
  answer: string
}

const props = defineProps<{ messages: Message[] }>()

const emit = defineEmits<{
  submit: [question: string]
}>()

const question = ref('')

const handleSubmit = () => {
  if (!question.value.trim()) return
  emit('submit', question.value)
  question.value = ''
}
</script>

<style scoped>
.conversation-panel {
  background: #fff;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.messages {
  max-height: 400px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.prompt {
  display: flex;
  gap: 0.75rem;
}

.prompt input {
  flex: 1;
  padding: 0.5rem 0.75rem;
  border-radius: 4px;
  border: 1px solid #d1d5db;
}

.prompt button {
  padding: 0.5rem 1.5rem;
  border: none;
  border-radius: 4px;
  background: #2563eb;
  color: #fff;
  cursor: pointer;
}
</style>
