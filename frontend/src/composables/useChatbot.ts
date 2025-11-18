/**
 * Chatbot Composable
 * 
 * Manages chatbot conversations and messaging
 */
import { ref, computed } from 'vue'
import api from '@/services/api'

export interface ChatMessage {
  id: string
  conversation_id: string
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

export interface Conversation {
  id: string
  title: string
  created_at: string
  updated_at: string
}

export function useChatbot() {
  const conversations = ref<Conversation[]>([])
  const currentConversation = ref<Conversation | null>(null)
  const messages = ref<ChatMessage[]>([])
  const isLoading = ref(false)

  // Create new conversation
  const createConversation = async (title?: string) => {
    try {
      const response = await api.post('/api/v1/chatbot/conversations', {
        title,
      })
      currentConversation.value = response.data
      messages.value = []
      await fetchConversations()
      return response.data
    } catch (error) {
      console.error('Failed to create conversation:', error)
      throw error
    }
  }

  // Fetch all conversations
  const fetchConversations = async () => {
    try {
      const response = await api.get('/api/v1/chatbot/conversations')
      conversations.value = response.data
    } catch (error) {
      console.error('Failed to fetch conversations:', error)
    }
  }

  // Load conversation messages
  const loadConversation = async (conversationId: string) => {
    try {
      isLoading.value = true

      // Fetch conversation details
      const convResponse = await api.get(`/api/v1/chatbot/conversations/${conversationId}/messages`)
      const conv = conversations.value.find((c) => c.id === conversationId)
      
      if (conv) {
        currentConversation.value = conv
      }

      messages.value = convResponse.data
    } catch (error) {
      console.error('Failed to load conversation:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  // Send message
  const sendMessage = async (content: string) => {
    if (!currentConversation.value) {
      // Create new conversation if none exists
      await createConversation()
    }

    if (!currentConversation.value) {
      throw new Error('No active conversation')
    }

    try {
      isLoading.value = true

      // Add user message to UI immediately
      const userMessage: ChatMessage = {
        id: 'temp-' + Date.now(),
        conversation_id: currentConversation.value.id,
        role: 'user',
        content,
        created_at: new Date().toISOString(),
      }
      messages.value.push(userMessage)

      // Send to backend
      const response = await api.post(
        `/api/v1/chatbot/conversations/${currentConversation.value.id}/messages`,
        { content }
      )

      // Replace temp message with actual message and add assistant response
      messages.value = messages.value.filter((m) => m.id !== userMessage.id)
      
      // The response is the assistant's message
      messages.value.push(response.data)

      // Update conversations list
      await fetchConversations()
    } catch (error) {
      console.error('Failed to send message:', error)
      // Remove temp message on error
      messages.value = messages.value.filter((m) => !m.id.startsWith('temp-'))
      throw error
    } finally {
      isLoading.value = false
    }
  }

  // Delete conversation
  const deleteConversation = async (conversationId: string) => {
    try {
      await api.delete(`/api/v1/chatbot/conversations/${conversationId}`)
      
      if (currentConversation.value?.id === conversationId) {
        currentConversation.value = null
        messages.value = []
      }
      
      await fetchConversations()
    } catch (error) {
      console.error('Failed to delete conversation:', error)
      throw error
    }
  }

  // Clear current conversation
  const clearConversation = () => {
    currentConversation.value = null
    messages.value = []
  }

  // Get latest message
  const latestMessage = computed(() => {
    return messages.value[messages.value.length - 1]
  })

  return {
    conversations,
    currentConversation,
    messages,
    isLoading,
    latestMessage,
    createConversation,
    fetchConversations,
    loadConversation,
    sendMessage,
    deleteConversation,
    clearConversation,
  }
}
