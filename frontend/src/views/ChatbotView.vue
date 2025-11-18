<template>
  <div class="chatbot-view">
    <div class="view-header">
      <h1>Chatbot Assistant</h1>
      <p class="subtitle">Ask questions about robot control, data collection, and machine learning</p>
    </div>

    <div class="chatbot-layout">
      <!-- Conversations Sidebar -->
      <div class="sidebar">
        <div class="sidebar-header">
          <h2>Conversations</h2>
          <button @click="handleNewConversation" class="btn-new">
            <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 4v16m8-8H4"
              />
            </svg>
            New
          </button>
        </div>

        <div class="conversations-list">
          <div
            v-for="conv in conversations"
            :key="conv.id"
            class="conversation-item"
            :class="{ active: currentConversation?.id === conv.id }"
            @click="handleLoadConversation(conv.id)"
          >
            <div class="conversation-icon">
              <svg fill="currentColor" viewBox="0 0 20 20">
                <path
                  d="M2 5a2 2 0 012-2h7a2 2 0 012 2v4a2 2 0 01-2 2H9l-3 3v-3H4a2 2 0 01-2-2V5z"
                />
                <path
                  d="M15 7v2a4 4 0 01-4 4H9.828l-1.766 1.767c.28.149.599.233.938.233h2l3 3v-3h2a2 2 0 002-2V9a2 2 0 00-2-2h-1z"
                />
              </svg>
            </div>
            <div class="conversation-info">
              <div class="conversation-title">{{ conv.title }}</div>
              <div class="conversation-date">{{ formatDate(conv.updated_at) }}</div>
            </div>
            <button
              @click.stop="handleDeleteConversation(conv.id)"
              class="btn-delete-conv"
              title="Delete conversation"
            >
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
            </button>
          </div>

          <div v-if="conversations.length === 0" class="empty-conversations">
            <svg class="empty-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
              />
            </svg>
            <p>No conversations yet</p>
            <p class="empty-hint">Start a new conversation to begin chatting</p>
          </div>
        </div>
      </div>

      <!-- Chat Window -->
      <div class="chat-section">
        <div v-if="!currentConversation" class="welcome-screen">
          <div class="welcome-content">
            <svg class="welcome-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
              />
            </svg>
            <h2>Welcome to Chatbot Assistant</h2>
            <p>I can help you with:</p>
            <div class="feature-grid">
              <div class="feature-card">
                <svg class="feature-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"
                  />
                </svg>
                <h3>Robot Control</h3>
                <p>Navigate, control movement, and monitor status</p>
              </div>
              <div class="feature-card">
                <svg class="feature-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"
                  />
                </svg>
                <h3>Data Collection</h3>
                <p>Recording sessions and dataset management</p>
              </div>
              <div class="feature-card">
                <svg class="feature-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                  />
                </svg>
                <h3>ML Training</h3>
                <p>Model training, evaluation, and optimization</p>
              </div>
            </div>
            <button @click="handleNewConversation" class="btn-start">
              Start New Conversation
            </button>
          </div>
        </div>

        <ChatWindow
          v-else
          :messages="messages"
          :isLoading="isLoading"
          @send="handleSendMessage"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useChatbot } from '@/composables/useChatbot'
import ChatWindow from '@/components/chatbot/ChatWindow.vue'

const {
  conversations,
  currentConversation,
  messages,
  isLoading,
  createConversation,
  fetchConversations,
  loadConversation,
  sendMessage,
  deleteConversation,
  clearConversation,
} = useChatbot()

const handleNewConversation = async () => {
  try {
    await createConversation()
  } catch (error) {
    alert('Failed to create conversation')
  }
}

const handleLoadConversation = async (conversationId: string) => {
  try {
    await loadConversation(conversationId)
  } catch (error) {
    alert('Failed to load conversation')
  }
}

const handleSendMessage = async (content: string) => {
  try {
    await sendMessage(content)
  } catch (error) {
    alert('Failed to send message')
  }
}

const handleDeleteConversation = async (conversationId: string) => {
  if (!confirm('Are you sure you want to delete this conversation?')) return

  try {
    await deleteConversation(conversationId)
  } catch (error) {
    alert('Failed to delete conversation')
  }
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days === 0) {
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
  } else if (days === 1) {
    return 'Yesterday'
  } else if (days < 7) {
    return `${days} days ago`
  } else {
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }
}

onMounted(() => {
  fetchConversations()
})
</script>

<style scoped>
.chatbot-view {
  padding: 2rem;
  height: calc(100vh - 4rem);
  display: flex;
  flex-direction: column;
}

.view-header {
  margin-bottom: 1.5rem;
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

.chatbot-layout {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 1.5rem;
  flex: 1;
  min-height: 0;
}

@media (max-width: 1024px) {
  .chatbot-layout {
    grid-template-columns: 1fr;
  }
  
  .sidebar {
    display: none;
  }
}

.sidebar {
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.sidebar-header h2 {
  margin: 0;
  font-size: 1.125rem;
  color: #1f2937;
}

.btn-new {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.375rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  background: white;
  color: #374151;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-new:hover {
  background: #f9fafb;
}

.icon {
  width: 1rem;
  height: 1rem;
}

.conversations-list {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem;
}

.conversation-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: background 0.2s;
  position: relative;
}

.conversation-item:hover {
  background: #f9fafb;
}

.conversation-item.active {
  background: #eff6ff;
}

.conversation-icon {
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  background: #e0e7ff;
  color: #4f46e5;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.conversation-icon svg {
  width: 1.25rem;
  height: 1.25rem;
}

.conversation-info {
  flex: 1;
  min-width: 0;
}

.conversation-title {
  font-size: 0.875rem;
  font-weight: 500;
  color: #1f2937;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.conversation-date {
  font-size: 0.75rem;
  color: #9ca3af;
}

.btn-delete-conv {
  opacity: 0;
  width: 1.5rem;
  height: 1.5rem;
  padding: 0;
  border: none;
  background: none;
  color: #ef4444;
  cursor: pointer;
  flex-shrink: 0;
  transition: opacity 0.2s;
}

.conversation-item:hover .btn-delete-conv {
  opacity: 1;
}

.btn-delete-conv:hover {
  color: #dc2626;
}

.btn-delete-conv svg {
  width: 1.25rem;
  height: 1.25rem;
}

.empty-conversations {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  text-align: center;
  color: #9ca3af;
}

.empty-icon {
  width: 48px;
  height: 48px;
  margin-bottom: 1rem;
}

.empty-conversations p {
  margin: 0.25rem 0;
  font-size: 0.875rem;
}

.empty-hint {
  font-size: 0.75rem;
}

.chat-section {
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.welcome-screen {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  height: 100%;
}

.welcome-content {
  max-width: 800px;
  text-align: center;
}

.welcome-icon {
  width: 80px;
  height: 80px;
  color: #3b82f6;
  margin: 0 auto 1.5rem;
}

.welcome-content h2 {
  margin: 0 0 0.5rem 0;
  font-size: 1.875rem;
  color: #1f2937;
}

.welcome-content > p {
  margin: 0 0 2rem 0;
  color: #6b7280;
  font-size: 1.125rem;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
  margin-bottom: 2rem;
}

@media (max-width: 768px) {
  .feature-grid {
    grid-template-columns: 1fr;
  }
}

.feature-card {
  padding: 1.5rem;
  background: #f9fafb;
  border-radius: 0.5rem;
  border: 1px solid #e5e7eb;
}

.feature-icon {
  width: 2rem;
  height: 2rem;
  color: #3b82f6;
  margin-bottom: 0.75rem;
}

.feature-card h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1rem;
  color: #1f2937;
}

.feature-card p {
  margin: 0;
  font-size: 0.875rem;
  color: #6b7280;
  line-height: 1.5;
}

.btn-start {
  padding: 0.75rem 2rem;
  border: none;
  border-radius: 0.5rem;
  background: #3b82f6;
  color: white;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-start:hover {
  background: #2563eb;
}
</style>
