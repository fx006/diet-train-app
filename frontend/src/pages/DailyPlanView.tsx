import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import dayjs from 'dayjs'
import { plansApi } from '../api/plans'
import type { Plan } from '../types/plan'
import EditPlanModal from '../components/EditPlanModal'
import ConfirmDialog from '../components/ConfirmDialog'

export default function DailyPlanView() {
  const [selectedDate, setSelectedDate] = useState(dayjs().format('YYYY-MM-DD'))

  // 获取计划数据
  const { data: plansData, isLoading: plansLoading, refetch: refetchPlans } = useQuery({
    queryKey: ['plans', selectedDate],
    queryFn: () => plansApi.getByDate(selectedDate)
  })

  // 获取统计数据
  const { data: statsData, isLoading: statsLoading } = useQuery({
    queryKey: ['stats', selectedDate],
    queryFn: () => plansApi.getStats(selectedDate)
  })

  const handlePreviousDay = () => {
    setSelectedDate(dayjs(selectedDate).subtract(1, 'day').format('YYYY-MM-DD'))
  }

  const handleNextDay = () => {
    setSelectedDate(dayjs(selectedDate).add(1, 'day').format('YYYY-MM-DD'))
  }

  const handleToday = () => {
    setSelectedDate(dayjs().format('YYYY-MM-DD'))
  }

  const isLoading = plansLoading || statsLoading

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-4xl mx-auto">
        {/* 标题 */}
        <h1 className="text-3xl font-bold text-gray-900 mb-6">每日计划</h1>

        {/* 日期选择器 */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="flex items-center justify-between">
            <button
              onClick={handlePreviousDay}
              className="px-4 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded"
            >
              ← 前一天
            </button>

            <div className="flex items-center gap-4">
              <h2 className="text-xl font-semibold text-gray-900">
                {dayjs(selectedDate).format('YYYY年MM月DD日')}
              </h2>
              <button
                onClick={handleToday}
                className="px-3 py-1 text-sm text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded"
              >
                今天
              </button>
            </div>

            <button
              onClick={handleNextDay}
              className="px-4 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded"
            >
              后一天 →
            </button>
          </div>
        </div>

        {isLoading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-2 text-gray-600">加载中...</p>
          </div>
        ) : (
          <>
            {/* 统计卡片 */}
            {statsData && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-white rounded-lg shadow p-4">
                  <p className="text-sm text-gray-600">热量摄入</p>
                  <p className="text-2xl font-bold text-green-600">
                    {statsData.total_calories_intake}
                  </p>
                  <p className="text-xs text-gray-500">卡路里</p>
                </div>

                <div className="bg-white rounded-lg shadow p-4">
                  <p className="text-sm text-gray-600">热量消耗</p>
                  <p className="text-2xl font-bold text-orange-600">
                    {statsData.total_calories_burned}
                  </p>
                  <p className="text-xs text-gray-500">卡路里</p>
                </div>

                <div className="bg-white rounded-lg shadow p-4">
                  <p className="text-sm text-gray-600">净热量</p>
                  <p className={`text-2xl font-bold ${statsData.net_calories > 0 ? 'text-red-600' : 'text-blue-600'}`}>
                    {statsData.net_calories > 0 ? '+' : ''}{statsData.net_calories}
                  </p>
                  <p className="text-xs text-gray-500">卡路里</p>
                </div>

                <div className="bg-white rounded-lg shadow p-4">
                  <p className="text-sm text-gray-600">完成率</p>
                  <p className="text-2xl font-bold text-purple-600">
                    {statsData.completion_rate}%
                  </p>
                  <p className="text-xs text-gray-500">
                    {statsData.completed_items}/{statsData.total_items} 项
                  </p>
                </div>
              </div>
            )}

            {/* 餐食列表 */}
            <div className="bg-white rounded-lg shadow mb-6">
              <div className="p-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">餐食计划</h3>
              </div>
              <div className="p-4">
                {plansData && plansData.meals.length > 0 ? (
                  <div className="space-y-3">
                    {plansData.meals.map((meal) => (
                      <PlanItem key={meal.id} plan={meal} onUpdate={refetchPlans} />
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 text-center py-8">暂无餐食计划</p>
                )}
              </div>
            </div>

            {/* 运动列表 */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">运动计划</h3>
              </div>
              <div className="p-4">
                {plansData && plansData.exercises.length > 0 ? (
                  <div className="space-y-3">
                    {plansData.exercises.map((exercise) => (
                      <PlanItem key={exercise.id} plan={exercise} onUpdate={refetchPlans} />
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 text-center py-8">暂无运动计划</p>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

// 计划项组件
function PlanItem({ plan, onUpdate }: { plan: Plan; onUpdate: () => void }) {
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  const handleToggleComplete = async () => {
    try {
      if (plan.completed) {
        await plansApi.markUncomplete(plan.id)
      } else {
        await plansApi.markComplete(plan.id)
      }
      onUpdate()
    } catch (error) {
      console.error('Failed to toggle completion:', error)
    }
  }

  const handleSave = async (planData: Partial<Plan>) => {
    await plansApi.update(plan.id, planData)
    onUpdate()
  }

  const handleDelete = async () => {
    setIsDeleting(true)
    try {
      await plansApi.delete(plan.id)
      onUpdate()
      setIsDeleteDialogOpen(false)
    } catch (error) {
      console.error('Failed to delete plan:', error)
      alert('删除失败，请重试')
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <>
      <div className={`flex items-center justify-between p-3 rounded-lg border ${
        plan.completed ? 'bg-green-50 border-green-200' : 'bg-white border-gray-200'
      }`}>
        <div className="flex items-center gap-3 flex-1">
          <input
            type="checkbox"
            checked={plan.completed}
            onChange={handleToggleComplete}
            className="w-5 h-5 text-blue-600 rounded focus:ring-blue-500"
          />
          <div className="flex-1">
            <p className={`font-medium ${plan.completed ? 'line-through text-gray-500' : 'text-gray-900'}`}>
              {plan.name}
            </p>
            <div className="flex items-center gap-4 mt-1 text-sm text-gray-600">
              <span>{plan.calories} 卡路里</span>
              {plan.duration && <span>{plan.duration} 分钟</span>}
              {plan.actual_duration && (
                <span className="text-green-600">实际: {plan.actual_duration} 分钟</span>
              )}
            </div>
          </div>
        </div>

        {/* 操作按钮 */}
        <div className="flex gap-2 ml-3">
          <button
            onClick={() => setIsEditModalOpen(true)}
            className="px-3 py-1 text-sm text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded"
          >
            编辑
          </button>
          <button
            onClick={() => setIsDeleteDialogOpen(true)}
            className="px-3 py-1 text-sm text-red-600 hover:text-red-700 hover:bg-red-50 rounded"
          >
            删除
          </button>
        </div>
      </div>

      {/* 编辑模态框 */}
      <EditPlanModal
        plan={plan}
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        onSave={handleSave}
      />

      {/* 删除确认对话框 */}
      <ConfirmDialog
        isOpen={isDeleteDialogOpen}
        title="确认删除"
        message={`确定要删除"${plan.name}"吗？此操作无法撤销。`}
        confirmText="删除"
        cancelText="取消"
        onConfirm={handleDelete}
        onCancel={() => setIsDeleteDialogOpen(false)}
        isLoading={isDeleting}
      />
    </>
  )
}
