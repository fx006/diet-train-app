import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { aiApi, type Message, type GeneratePlanResponse } from '../api/ai'
import { plansApi } from '../api/plans'
import dayjs from 'dayjs'

export default function AIChatPage() {
  const navigate = useNavigate()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [conversationId, setConversationId] = useState<number>()
  const [generatedPlan, setGeneratedPlan] = useState<GeneratePlanResponse | null>(null)
  const [showPlanPreview, setShowPlanPreview] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const [lastFailedMessage, setLastFailedMessage] = useState<string>('')

  const chatMutation = useMutation({
    mutationFn: (message: string) => aiApi.chat(message, conversationId?.toString()),
    retry: 2, // 自动重试2次
    retryDelay: 1000, // 重试延迟1秒
    onSuccess: (data) => {
      const response = data.message
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: response,
          timestamp: data.timestamp
        }
      ])
      if (data.conversation_id) {
        setConversationId(data.conversation_id)
      }
      
      // 清除失败消息
      setLastFailedMessage('')
      
      // 检测是否包含计划生成的关键词
      if (response && (response.includes('计划') || response.includes('餐食') || response.includes('运动'))) {
        // 尝试解析计划数据（这里简化处理，实际应该从后端返回结构化数据）
        tryExtractPlan(response)
      }
    },
    onError: (error: any, variables) => {
      // 保存失败的消息以便重试
      setLastFailedMessage(variables)
      
      const errorMessage = error.response?.data?.detail?.message || error.message || '网络错误，请检查连接'
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: `❌ 抱歉，发生了错误：${errorMessage}`,
          timestamp: new Date().toISOString()
        }
      ])
    }
  })

  const generatePlanMutation = useMutation({
    mutationFn: ({ date, requirements }: { date: string; requirements?: string }) =>
      aiApi.generatePlan(date, requirements),
    retry: 1, // 重试1次
    retryDelay: 1500,
    onSuccess: (data) => {
      setGeneratedPlan(data)
      setShowPlanPreview(true)
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail?.message || error.message || '生成失败'
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: `❌ 生成计划失败：${errorMessage}\n\n💡 提示：你可以尝试在对话中描述你的需求，我会帮你生成计划。`,
          timestamp: new Date().toISOString()
        }
      ])
    }
  })

  const savePlanMutation = useMutation({
    mutationFn: async (plan: GeneratePlanResponse) => {
      const date = dayjs().format('YYYY-MM-DD')
      const promises = []
      
      // 保存餐食
      for (const meal of plan.plan.meals) {
        promises.push(
          plansApi.createPlan({
            date,
            type: 'meal',
            name: meal.name,
            calories: meal.calories,
            duration: 0
          })
        )
      }
      
      // 保存运动
      for (const exercise of plan.plan.exercises) {
        promises.push(
          plansApi.createPlan({
            date,
            type: 'exercise',
            name: exercise.name,
            calories: exercise.calories,
            duration: exercise.duration
          })
        )
      }
      
      await Promise.all(promises)
    },
    onSuccess: () => {
      setShowPlanPreview(false)
      setGeneratedPlan(null)
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: '✅ 计划已保存！你可以在"每日计划"页面查看。',
          timestamp: new Date().toISOString()
        }
      ])
    },
    onError: (error: any) => {
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: `保存计划失败：${error.response?.data?.detail?.message || '请稍后重试'}`,
          timestamp: new Date().toISOString()
        }
      ])
    }
  })

  const tryExtractPlan = (response: string) => {
    // 简化的计划提取逻辑
    // 实际应该从后端返回结构化数据
    // 这里只是示例
  }

  const handleSend = () => {
    if (!input.trim() || chatMutation.isPending) return

    const userMessage: Message = {
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    chatMutation.mutate(input.trim())
    setInput('')
  }

  const handleClearHistory = async () => {
    if (confirm('确定要清除所有对话历史吗？')) {
      try {
        await aiApi.clearHistory()
        setMessages([])
        setConversationId(undefined)
      } catch (error) {
        alert('清除历史失败')
      }
    }
  }

  const handleQuickGenerate = () => {
    const today = dayjs().format('YYYY-MM-DD')
    generatePlanMutation.mutate({ date: today })
  }

  const handleRetry = () => {
    if (lastFailedMessage) {
      chatMutation.mutate(lastFailedMessage)
    }
  }

  const handleConfirmPlan = () => {
    if (generatedPlan) {
      savePlanMutation.mutate(generatedPlan)
    }
  }

  const handleCancelPlan = () => {
    setShowPlanPreview(false)
    setGeneratedPlan(null)
  }

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* 顶部导航 */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate(-1)}
              className="text-gray-600 hover:text-gray-900"
            >
              ← 返回
            </button>
            <h1 className="text-2xl font-bold text-gray-900">AI 健身助手</h1>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleQuickGenerate}
              disabled={generatePlanMutation.isPending}
              className="px-4 py-2 text-sm bg-green-600 text-white hover:bg-green-700 rounded-lg disabled:opacity-50"
            >
              {generatePlanMutation.isPending ? '生成中...' : '快速生成计划'}
            </button>
            <button
              onClick={handleClearHistory}
              className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg"
            >
              清除历史
            </button>
          </div>
        </div>
      </div>

      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="max-w-4xl mx-auto space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">🤖</div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                你好！我是你的AI健身助手
              </h2>
              <p className="text-gray-600 mb-6">
                我可以帮你生成个性化的饮食和运动计划
              </p>
              <div className="max-w-md mx-auto text-left bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="font-semibold text-blue-900 mb-2">试试这些问题：</p>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• "帮我生成今天的饮食计划"</li>
                  <li>• "我想减脂，给我推荐运动"</li>
                  <li>• "我不喜欢西兰花，换个菜"</li>
                  <li>• "今天摄入了多少热量？"</li>
                </ul>
              </div>
            </div>
          )}

          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-lg p-4 ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white border border-gray-200 text-gray-900'
                }`}
              >
                <div className="whitespace-pre-wrap">{message.content}</div>
                {message.timestamp && (
                  <div
                    className={`text-xs mt-2 ${
                      message.role === 'user' ? 'text-blue-100' : 'text-gray-500'
                    }`}
                  >
                    {dayjs(message.timestamp).format('HH:mm')}
                  </div>
                )}
              </div>
            </div>
          ))}

          {chatMutation.isPending && (
            <div className="flex justify-start">
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <div className="flex items-center gap-2">
                  <div className="animate-bounce">●</div>
                  <div className="animate-bounce delay-100">●</div>
                  <div className="animate-bounce delay-200">●</div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* 输入框 */}
      <div className="bg-white border-t border-gray-200 p-4">
        <div className="max-w-4xl mx-auto">
          {lastFailedMessage && (
            <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center justify-between">
              <span className="text-sm text-red-800">
                上一条消息发送失败
              </span>
              <button
                onClick={handleRetry}
                disabled={chatMutation.isPending}
                className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
              >
                重试
              </button>
            </div>
          )}
          <div className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
              placeholder="输入你的问题或需求..."
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={chatMutation.isPending}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || chatMutation.isPending}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              发送
            </button>
          </div>
        </div>
      </div>

      {/* 计划预览模态框 */}
      {showPlanPreview && generatedPlan && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                📋 生成的计划预览
              </h2>

              {/* 说明 */}
              {generatedPlan.explanation && (
                <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-sm text-blue-900">{generatedPlan.explanation}</p>
                </div>
              )}

              {/* 餐食计划 */}
              {generatedPlan.plan.meals.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">
                    🍽️ 餐食计划
                  </h3>
                  <div className="space-y-2">
                    {generatedPlan.plan.meals.map((meal, index) => (
                      <div
                        key={index}
                        className="flex justify-between items-center p-3 bg-gray-50 rounded-lg"
                      >
                        <div>
                          <div className="font-medium text-gray-900">{meal.name}</div>
                          {meal.time && (
                            <div className="text-sm text-gray-600">{meal.time}</div>
                          )}
                        </div>
                        <div className="text-green-600 font-semibold">
                          {meal.calories} 卡路里
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 运动计划 */}
              {generatedPlan.plan.exercises.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">
                    🏃 运动计划
                  </h3>
                  <div className="space-y-2">
                    {generatedPlan.plan.exercises.map((exercise, index) => (
                      <div
                        key={index}
                        className="flex justify-between items-center p-3 bg-gray-50 rounded-lg"
                      >
                        <div>
                          <div className="font-medium text-gray-900">{exercise.name}</div>
                          <div className="text-sm text-gray-600">
                            {exercise.duration} 分钟
                          </div>
                        </div>
                        <div className="text-orange-600 font-semibold">
                          -{exercise.calories} 卡路里
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 操作按钮 */}
              <div className="flex gap-3 mt-6">
                <button
                  onClick={handleConfirmPlan}
                  disabled={savePlanMutation.isPending}
                  className="flex-1 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 font-medium"
                >
                  {savePlanMutation.isPending ? '保存中...' : '✓ 确认并保存'}
                </button>
                <button
                  onClick={handleCancelPlan}
                  disabled={savePlanMutation.isPending}
                  className="flex-1 px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50 font-medium"
                >
                  ✕ 取消
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
