import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { historyApi, type HistoryDate, type HistoryStats } from '../api/history'

export default function HistoryPage() {
  const navigate = useNavigate()
  const [historyDates, setHistoryDates] = useState<HistoryDate[]>([])
  const [stats, setStats] = useState<HistoryStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [isExporting, setIsExporting] = useState(false)

  useEffect(() => {
    loadHistory()
    loadStats()
  }, [])

  const loadHistory = async (start?: string, end?: string) => {
    setIsLoading(true)
    setError('')
    try {
      const dates = await historyApi.getHistory(start, end)
      setHistoryDates(dates)
    } catch (err: any) {
      setError(err.response?.data?.detail?.message || '加载历史记录失败')
    } finally {
      setIsLoading(false)
    }
  }

  const loadStats = async () => {
    try {
      const statsData = await historyApi.getStats()
      setStats(statsData)
    } catch (err) {
      console.error('Failed to load stats:', err)
    }
  }

  const handleFilter = () => {
    loadHistory(startDate, endDate)
  }

  const handleClearFilter = () => {
    setStartDate('')
    setEndDate('')
    loadHistory()
  }

  const handleExport = async (format: 'excel' | 'csv') => {
    setIsExporting(true)
    try {
      const blob = await historyApi.exportData(format)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `diet-training-history.${format === 'excel' ? 'xlsx' : 'csv'}`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err: any) {
      alert(err.response?.data?.detail?.message || '导出失败，请重试')
    } finally {
      setIsExporting(false)
    }
  }

  const handleViewDate = (date: string) => {
    navigate(`/plans?date=${date}`)
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-6xl mx-auto">
        {/* 返回按钮 */}
        <button
          onClick={() => navigate('/')}
          className="mb-6 text-gray-600 hover:text-gray-900 flex items-center gap-2"
        >
          ← 返回首页
        </button>

        {/* 标题 */}
        <h1 className="text-3xl font-bold text-gray-900 mb-6">历史记录</h1>

        {/* 统计卡片 */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm text-gray-600 mb-1">总训练天数</div>
              <div className="text-3xl font-bold text-blue-600">{stats.total_training_days}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm text-gray-600 mb-1">总运动时长</div>
              <div className="text-3xl font-bold text-green-600">
                {stats.total_exercise_duration}
              </div>
              <div className="text-xs text-gray-500">分钟</div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm text-gray-600 mb-1">总热量消耗</div>
              <div className="text-3xl font-bold text-orange-600">
                {stats.total_calories_burned.toLocaleString()}
              </div>
              <div className="text-xs text-gray-500">卡路里</div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm text-gray-600 mb-1">平均完成率</div>
              <div className="text-3xl font-bold text-purple-600">
                {stats.average_completion_rate.toFixed(1)}%
              </div>
            </div>
          </div>
        )}

        {/* 过滤和导出 */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex flex-col md:flex-row gap-4 items-end">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                开始日期
              </label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                结束日期
              </label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleFilter}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                筛选
              </button>
              <button
                onClick={handleClearFilter}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              >
                清除
              </button>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => handleExport('excel')}
                disabled={isExporting}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                导出Excel
              </button>
              <button
                onClick={() => handleExport('csv')}
                disabled={isExporting}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                导出CSV
              </button>
            </div>
          </div>
        </div>

        {/* 错误提示 */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg">
            {error}
          </div>
        )}

        {/* 历史记录列表 */}
        <div className="bg-white rounded-lg shadow">
          {isLoading ? (
            <div className="p-8 text-center text-gray-500">
              <div className="inline-block w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-4"></div>
              <p>加载中...</p>
            </div>
          ) : historyDates.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <div className="text-4xl mb-4">📅</div>
              <p className="text-lg font-medium mb-2">暂无历史记录</p>
              <p className="text-sm">开始记录你的饮食和运动计划吧！</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      日期
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      餐食数量
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      运动数量
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      热量摄入
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      热量消耗
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      净热量
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      操作
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {historyDates.map((record) => (
                    <tr key={record.date} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {new Date(record.date).toLocaleDateString('zh-CN', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric'
                        })}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {record.meal_count} 项
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {record.exercise_count} 项
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600 font-medium">
                        +{record.total_calories_in}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-orange-600 font-medium">
                        -{record.total_calories_out}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <span
                          className={
                            record.net_calories > 0
                              ? 'text-red-600'
                              : record.net_calories < 0
                              ? 'text-blue-600'
                              : 'text-gray-600'
                          }
                        >
                          {record.net_calories > 0 ? '+' : ''}
                          {record.net_calories}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <button
                          onClick={() => handleViewDate(record.date)}
                          className="text-blue-600 hover:text-blue-800 font-medium"
                        >
                          查看详情
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* 提示信息 */}
        {historyDates.length > 0 && (
          <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-800">
              💡 提示：点击"查看详情"可以查看该日期的完整计划和统计信息
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
