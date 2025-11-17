import { ref } from 'vue'

import { chatbotApi } from '../../shared/services/apiClient'

interface ChatMessage {
  id: string
  question: string
  answer: string
}

export function useChatbot() {
  const messages = ref<ChatMessage[]>([])

  const ask = async (question: string) => {
    const response = await chatbotApi.query(question)
    messages.value.push({
      id: crypto.randomUUID(),
      question,
      answer: response.answer,
    })
  }

  return {
    messages,
    ask,
  }
}
