import { useState, useEffect } from 'react'
import type { Plan } from '../types/plan'

interface EditPlanModalProps {
  plan: Plan
  isOpen: boolean
  onClose: () => void
  onSave: (planData: Partial<Plan>) => Promise<void>
}

export default function EditPlanModal({ plan, isOpen, onClose, onSave }: EditPlanModalProps) {
  const [formData, setFormData] = useState({
    name: plan.name,
    calories: plan.calories.toString(),
    duration: plan.duration?.toString() || '',
    actual_duration: plan.actual_duration?.toString() || ''
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (isOpen) {
      setFormData({
        name: plan.name,
        calories: plan.calories.toString(),
        duration: plan.duration?.toString() || '',
        actual_duration: plan.actual_duration?.toString() || ''
      })
      setError('')
    }
  }, [isOpen, plan])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    // 验证
    if (!formData.name.trim()) {
      setError('名称不能为空')
      return
    }

    const calories = parseFloat(formData.calories)
    if (isNaN(calories) || calories < 0) {
      setError('热量必须是非负数')
      return
    }

    const duration = formData.duration ? parseInt(formData.duration) : undefined
    if (duration !== undefined && (isNaN(duration) || duration < 0)) {
      setError('时长必须是非负整数')
      return
    }

    const actualDuration = formData.actual_duration ? parseInt(formData.actual_duration) : undefined
    if (actualDuration !== undefined && (isNaN(actualDuration) || actualDuration < 0)) {
      setError('实际时长必须是非负整数')
      return
    }

    setIsSubmitting(true)
    try {
      await onSave({
        name: formData.name.trim(),
        calories,
        duration,
        actual_duration: actualDuration
      })
      onClose()
    } catch (err: any) {
      setError(err.response?.data?.detail?.message || '保存失败，请重试')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
        <div className="p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">编辑计划</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* 名称 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                名称 *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="例如：早餐、跑步"
              />
            </div>

            {/* 热量 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                热量（卡路里）*
              </label>
              <input
                type="number"
                step="0.1"
                value={formData.calories}
                onChange={(e) => setFormData({ ...formData, calories: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="例如：500"
              />
            </div>

            {/* 计划时长（仅运动） */}
            {plan.type === 'exercise' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  计划时长（分钟）
                </label>
                <input
                  type="number"
                  value={formData.duration}
                  onChange={(e) => setFormData({ ...formData, duration: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="例如：30"
                />
              </div>
            )}

            {/* 实际时长（仅运动） */}
            {plan.type === 'exercise' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  实际时长（分钟）
                </label>
                <input
                  type="number"
                  value={formData.actual_duration}
                  onChange={(e) => setFormData({ ...formData, actual_duration: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="例如：35"
                />
              </div>
            )}

            {/* 错误信息 */}
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                {error}
              </div>
            )}

            {/* 按钮 */}
            <div className="flex gap-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                disabled={isSubmitting}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50"
              >
                取消
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {isSubmitting ? '保存中...' : '保存'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
