/**
 * Type definitions for the application.
 */

export interface PlanItem {
  id?: number
  date: string
  type: 'meal' | 'exercise'
  name: string
  calories: number
  duration?: number // minutes, for exercise only
  completed?: boolean
  actual_duration?: number
}

export interface DailyStats {
  date: string
  total_calories_intake: number
  total_calories_burned: number
  net_calories: number
  total_exercise_duration: number
  completion_rate: number
}

export interface AIMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

export interface GeneratedPlan {
  date: string
  meals: PlanItem[]
  exercises: PlanItem[]
  reasoning: string
}

export interface UserPreference {
  key: string
  value: string
}
