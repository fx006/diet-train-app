import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp?: string
}

export interface ChatResponse {
  message: string
  conversation_id: number
  timestamp: string
}

export interface GeneratePlanResponse {
  plan: {
    meals: Array<{
      name: string
      calories: number
      time?: string
    }>
    exercises: Array<{
      name: string
      duration: number
      calories: number
    }>
  }
  explanation: string
}

export const aiApi = {
  // AI对话
  chat: async (message: string, conversationId?: string): Promise<ChatResponse> => {
    const response = await axios.post(`${API_BASE_URL}/api/ai/chat`, {
      message,
      conversation_id: conversationId
    })
    return response.data
  },

  // 生成计划
  generatePlan: async (date: string, requirements?: string): Promise<GeneratePlanResponse> => {
    const response = await axios.post(`${API_BASE_URL}/api/ai/generate-plan`, {
      date,
      requirements
    })
    return response.data
  },

  // 获取对话历史
  getHistory: async () => {
    const response = await axios.get(`${API_BASE_URL}/api/ai/history`)
    return response.data
  },

  // 清除对话历史
  clearHistory: async () => {
    const response = await axios.delete(`${API_BASE_URL}/api/ai/history`)
    return response.data
  }
}
