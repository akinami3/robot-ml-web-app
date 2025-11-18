<template>
  <div class="chat-window">
    <div class="messages-container" ref="messagesContainer">
      <div
        v-for="message in messages"
        :key="message.id"
        class="message"
        :class="{ 'message-user': message.role === 'user', 'message-assistant': message.role === 'assistant' }"
      >
        <div class="message-avatar">
          <svg v-if="message.role === 'user'" class="avatar-icon" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd" />
          </svg>
          <svg v-else class="avatar-icon" fill="currentColor" viewBox="0 0 20 20">
            <path d="M2 5a2 2 0 012-2h7a2 2 0 012 2v4a2 2 0 01-2 2H9l-3 3v-3H4a2 2 0 01-2-2V5z" />
            <path d="M15 7v2a4 4 0 01-4 4H9.828l-1.766 1.767c.28.149.599.233.938.233h2l3 3v-3h2a2 2 0 002-2V9a2 2 0 00-2-2h-1z" />
          </svg>
        </div>
        <div class="message-content">
          <div class="message-header">
            <span class="message-role">{{ message.role === 'user' ? 'You' : 'Assistant' }}</span>
            <span class="message-time">{{ formatTime(message.created_at) }}</span>
          </div>
          <div class="message-text">{{ message.content }}</div>
        </div>
      </div>

      <div v-if="isLoading" class="message message-assistant">
        <div class="message-avatar">
          <svg class="avatar-icon" fill="currentColor" viewBox="0 0 20 20">
            <path d="M2 5a2 2 0 012-2h7a2 2 0 012 2v4a2 2 0 01-2 2H9l-3 3v-3H4a2 2 0 01-2-2V5z" />
          </svg>
        </div>
        <div class="message-content">
          <div class="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      </div>
    </div>

    <form @submit.prevent="handleSubmit" class="input-form">
      <input
        v-model="inputMessage"
        type="text"
        placeholder="Type your message..."
        class="message-input"
        :disabled="isLoading"
      />
      <button type="submit" class="send-button" :disabled="!inputMessage.trim() || isLoading">
        <svg class="send-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
        </svg>
      </button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

const props = defineProps<{
  messages: ChatMessage[]
  isLoading: boolean
}>()

const emit = defineEmits<{
  send: [message: string]
}>()

const inputMessage = ref('')
const messagesContainer = ref<HTMLElement | null>(null)

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const formatTime = (timestamp: string) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
}

const handleSubmit = () => {
  if (!inputMessage.value.trim() || props.isLoading) return

  emit('send', inputMessage.value)
  inputMessage.value = ''
}

watch(
  () => props.messages.length,
  () => {
    scrollToBottom()
  }
)

watch(
  () => props.isLoading,
  () => {
    scrollToBottom()
  }
)
</script>

<style scoped>
.chat-window {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.message {
  display: flex;
  gap: 0.75rem;
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-avatar {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.message-user .message-avatar {
  background: #3b82f6;
  color: white;
}

.message-assistant .message-avatar {
  background: #10b981;
  color: white;
}

.avatar-icon {
  width: 20px;
  height: 20px;
}

.message-content {
  flex: 1;
  min-width: 0;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
}

.message-role {
  font-size: 0.875rem;
  font-weight: 600;
  color: #1f2937;
}

.message-time {
  font-size: 0.75rem;
  color: #9ca3af;
}

.message-text {
  font-size: 0.9375rem;
  line-height: 1.6;
  color: #374151;
  white-space: pre-wrap;
  word-break: break-word;
}

.typing-indicator {
  display: flex;
  gap: 0.25rem;
  padding: 0.5rem 0;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #9ca3af;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%,
  60%,
  100% {
    opacity: 0.3;
    transform: translateY(0);
  }
  30% {
    opacity: 1;
    transform: translateY(-10px);
  }
}

.input-form {
  display: flex;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid #e5e7eb;
  background: #f9fafb;
}

.message-input {
  flex: 1;
  padding: 0.625rem 1rem;
  border: 1px solid #d1d5db;
  border-radius: 1.5rem;
  font-size: 0.9375rem;
  transition: border-color 0.2s;
}

.message-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.message-input:disabled {
  background: #f3f4f6;
  cursor: not-allowed;
}

.send-button {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 50%;
  background: #3b82f6;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.send-button:hover:not(:disabled) {
  background: #2563eb;
}

.send-button:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.send-icon {
  width: 20px;
  height: 20px;
}
</style>
