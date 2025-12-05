import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export interface UserPreferences {
  goal?: string
  allergies: string[]
  dislikes: string[]
  target_calories?: number
  activity_level?: string
}

export const preferencesApi = {
  // 获取偏好
  get: async (): Promise<UserPreferences> => {
    const response = await axios.get(`${API_BASE_URL}/api/preferences`)
    return response.data
  },

  // 更新偏好
  update: async (preferences: Partial<UserPreferences>): Promise<UserPreferences> => {
    const response = await axios.put(`${API_BASE_URL}/api/preferences`, preferences)
    return response.data
  },

  // 删除所有偏好
  deleteAll: async () => {
    const response = await axios.delete(`${API_BASE_URL}/api/preferences`)
    return response.data
  }
}
