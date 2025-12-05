import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export interface HistoryDate {
  date: string
  meal_count: number
  exercise_count: number
  total_calories_in: number
  total_calories_out: number
  net_calories: number
}

export interface HistoryStats {
  start_date: string | null
  end_date: string | null
  total_training_days: number
  total_calories_burned: number
  total_exercise_duration: number
  average_daily_calories_burned: number
  average_daily_exercise_duration: number
  total_items: number
  completed_items: number
  average_completion_rate: number
}

export interface ExportFormat {
  format: 'excel' | 'csv'
}

export const historyApi = {
  // 获取历史记录日期列表
  getHistory: async (startDate?: string, endDate?: string): Promise<HistoryDate[]> => {
    const params = new URLSearchParams()
    if (startDate) params.append('start_date', startDate)
    if (endDate) params.append('end_date', endDate)
    
    const response = await axios.get(`${API_BASE_URL}/api/plans/history?${params}`)
    return response.data.dates || []
  },

  // 获取统计数据
  getStats: async (): Promise<HistoryStats> => {
    const response = await axios.get(`${API_BASE_URL}/api/plans/history/stats`)
    return response.data
  },

  // 导出数据
  exportData: async (format: 'excel' | 'csv'): Promise<Blob> => {
    const response = await axios.get(`${API_BASE_URL}/api/files/export/${format}`, {
      responseType: 'blob'
    })
    return response.data
  }
}
