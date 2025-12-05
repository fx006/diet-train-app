import { useNavigate } from 'react-router-dom'
import TimerComponent from '../components/TimerComponent'

export default function TimerPage() {
  const navigate = useNavigate()

  const handleComplete = (duration: number) => {
    alert(`运动完成！用时：${duration} 分钟`)
    // 可以在这里保存运动记录
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
        <h1 className="text-3xl font-bold text-gray-900 mb-6 text-center">运动计时器</h1>

        {/* 计时器组件 */}
        <TimerComponent onComplete={handleComplete} />

        {/* 使用说明 */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-semibold text-blue-900 mb-2">使用说明</h3>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• <strong>正计时</strong>：从零开始计时，适合记录运动时长</li>
            <li>• <strong>倒计时</strong>：设定时长后倒数，时间到时会有提示音</li>
            <li>• 可以随时暂停、继续或重置计时器</li>
            <li>• 点击"完成"按钮保存运动记录</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
