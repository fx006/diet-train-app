import axios from 'axios'
import type { DailyPlans, DailyStats } from '../types/plan'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const plansApi = {
  // 获取指定日期的计划
  getByDate: async (date: string): Promise<DailyPlans> => {
    const response = await axios.get(`${API_BASE_URL}/api/plans/${date}`)
    return response.data
  },

  // 获取指定日期的统计
  getStats: async (date: string): Promise<DailyStats> => {
    const response = await axios.get(`${API_BASE_URL}/api/plans/stats/${date}`)
    return response.data
  },

  // 创建计划
  create: async (planData: any) => {
    const response = await axios.post(`${API_BASE_URL}/api/plans`, planData)
    return response.data
  },

  // 更新计划
  update: async (id: number, planData: any) => {
    const response = await axios.put(`${API_BASE_URL}/api/plans/${id}`, planData)
    return response.data
  },

  // 删除计划
  delete: async (id: number) => {
    const response = await axios.delete(`${API_BASE_URL}/api/plans/${id}`)
    return response.data
  },

  // 标记完成
  markComplete: async (id: number, actualDuration?: number) => {
    const response = await axios.post(`${API_BASE_URL}/api/plans/${id}/complete`, {
      actual_duration: actualDuration
    })
    return response.data
  },

  // 取消完成
  markUncomplete: async (id: number) => {
    const response = await axios.post(`${API_BASE_URL}/api/plans/${id}/uncomplete`)
    return response.data
  }
}
