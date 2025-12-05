import { create } from 'zustand'
import dayjs, { Dayjs } from 'dayjs'

interface PlanStore {
  selectedDate: Dayjs
  setSelectedDate: (date: Dayjs) => void
}

export const usePlanStore = create<PlanStore>((set) => ({
  selectedDate: dayjs(),
  setSelectedDate: (date) => set({ selectedDate: date }),
}))
