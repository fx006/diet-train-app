export interface Plan {
  id: number
  date: string
  type: 'meal' | 'exercise'
  name: string
  calories: number
  duration?: number
  actual_duration?: number
  completed: boolean
  created_at?: string
  updated_at?: string
}

export interface DailyPlans {
  date: string
  meals: Plan[]
  exercises: Plan[]
  total_items: number
}

export interface DailyStats {
  date: string
  total_calories_intake: number
  total_calories_burned: number
  net_calories: number
  total_exercise_duration: number
  total_items: number
  completed_items: number
  completion_rate: number
}
