import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { preferencesApi } from '../api/preferences'

export default function PreferencesPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [formData, setFormData] = useState({
    goal: '',
    allergies: [] as string[],
    dislikes: [] as string[],
    target_calories: '',
    activity_level: ''
  })

  const [allergyInput, setAllergyInput] = useState('')
  const [dislikeInput, setDislikeInput] = useState('')
  const [saveSuccess, setSaveSuccess] = useState(false)

  // 获取偏好
  const { data: preferences, isLoading } = useQuery({
    queryKey: ['preferences'],
    queryFn: preferencesApi.get
  })

  // 更新偏好
  const updateMutation = useMutation({
    mutationFn: preferencesApi.update,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['preferences'] })
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 3000)
    }
  })

  // 加载偏好数据
  useEffect(() => {
    if (preferences) {
      setFormData({
        goal: preferences.goal || '',
        allergies: preferences.allergies || [],
        dislikes: preferences.dislikes || [],
        target_calories: preferences.target_calories?.toString() || '',
        activity_level: preferences.activity_level || ''
      })
    }
  }, [preferences])

  const handleAddAllergy = () => {
    if (allergyInput.trim() && !formData.allergies.includes(allergyInput.trim())) {
      setFormData({
        ...formData,
        allergies: [...formData.allergies, allergyInput.trim()]
      })
      setAllergyInput('')
    }
  }

  const handleRemoveAllergy = (allergy: string) => {
    setFormData({
      ...formData,
      allergies: formData.allergies.filter(a => a !== allergy)
    })
  }

  const handleAddDislike = () => {
    if (dislikeInput.trim() && !formData.dislikes.includes(dislikeInput.trim())) {
      setFormData({
        ...formData,
        dislikes: [...formData.dislikes, dislikeInput.trim()]
      })
      setDislikeInput('')
    }
  }

  const handleRemoveDislike = (dislike: string) => {
    setFormData({
      ...formData,
      dislikes: formData.dislikes.filter(d => d !== dislike)
    })
  }

  const handleSave = () => {
    const dataToSave: any = {
      goal: formData.goal || undefined,
      allergies: formData.allergies,
      dislikes: formData.dislikes,
      activity_level: formData.activity_level || undefined
    }

    if (formData.target_calories) {
      dataToSave.target_calories = parseInt(formData.target_calories)
    }

    updateMutation.mutate(dataToSave)
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">加载中...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-2xl mx-auto">
        {/* 返回按钮 */}
        <button
          onClick={() => navigate(-1)}
          className="mb-6 text-gray-600 hover:text-gray-900 flex items-center gap-2"
        >
          ← 返回
        </button>

        {/* 标题 */}
        <h1 className="text-3xl font-bold text-gray-900 mb-6">个人偏好设置</h1>

        <div className="bg-white rounded-lg shadow-lg p-6 space-y-6">
          {/* 目标 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              健身目标
            </label>
            <select
              value={formData.goal}
              onChange={(e) => setFormData({ ...formData, goal: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">请选择</option>
              <option value="减脂">减脂</option>
              <option value="增肌">增肌</option>
              <option value="维持">维持</option>
            </select>
          </div>

          {/* 活动水平 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              活动水平
            </label>
            <select
              value={formData.activity_level}
              onChange={(e) => setFormData({ ...formData, activity_level: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">请选择</option>
              <option value="低">低（久坐）</option>
              <option value="中等">中等（每周运动3-5次）</option>
              <option value="高">高（每周运动6-7次）</option>
            </select>
          </div>

          {/* 目标热量 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              目标热量（卡路里/天）
            </label>
            <input
              type="number"
              value={formData.target_calories}
              onChange={(e) => setFormData({ ...formData, target_calories: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="例如：2000"
            />
          </div>

          {/* 过敏食物 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              过敏食物
            </label>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                value={allergyInput}
                onChange={(e) => setAllergyInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleAddAllergy()}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="输入过敏食物，按回车添加"
              />
              <button
                onClick={handleAddAllergy}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                添加
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {formData.allergies.map((allergy) => (
                <span
                  key={allergy}
                  className="inline-flex items-center gap-1 px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm"
                >
                  {allergy}
                  <button
                    onClick={() => handleRemoveAllergy(allergy)}
                    className="hover:text-red-900"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          </div>

          {/* 不喜欢的食物 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              不喜欢的食物
            </label>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                value={dislikeInput}
                onChange={(e) => setDislikeInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleAddDislike()}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="输入不喜欢的食物，按回车添加"
              />
              <button
                onClick={handleAddDislike}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                添加
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {formData.dislikes.map((dislike) => (
                <span
                  key={dislike}
                  className="inline-flex items-center gap-1 px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm"
                >
                  {dislike}
                  <button
                    onClick={() => handleRemoveDislike(dislike)}
                    className="hover:text-yellow-900"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          </div>

          {/* 保存按钮 */}
          <div className="flex gap-3 pt-4">
            <button
              onClick={handleSave}
              disabled={updateMutation.isPending}
              className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium"
            >
              {updateMutation.isPending ? '保存中...' : '保存设置'}
            </button>
          </div>

          {/* 成功消息 */}
          {saveSuccess && (
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg text-green-800">
              ✓ 设置已保存
            </div>
          )}

          {/* 错误消息 */}
          {updateMutation.isError && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
              保存失败，请重试
            </div>
          )}
        </div>

        {/* 说明 */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-semibold text-blue-900 mb-2">关于偏好设置</h3>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• 这些设置将用于AI生成个性化的饮食和运动计划</li>
            <li>• 过敏食物会被完全排除在计划之外</li>
            <li>• 不喜欢的食物会尽量避免，但可能偶尔出现</li>
            <li>• 目标热量会影响每日计划的热量分配</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
