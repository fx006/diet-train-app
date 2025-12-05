import { Link } from 'react-router-dom'

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full">
        <div className="text-center mb-8 md:mb-12">
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold text-gray-900 mb-3 md:mb-4">
            饮食训练追踪器
          </h1>
          <p className="text-base sm:text-lg md:text-xl text-gray-600 px-4">
            记录你的饮食和运动，追踪你的健康目标
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
          <Link
            to="/plans"
            className="bg-white rounded-xl shadow-lg p-6 md:p-8 hover:shadow-xl transition-all hover:scale-105 active:scale-95"
          >
            <div className="text-3xl md:text-4xl mb-3 md:mb-4">📅</div>
            <h2 className="text-xl md:text-2xl font-bold text-gray-900 mb-2">每日计划</h2>
            <p className="text-sm md:text-base text-gray-600">
              查看和管理你的每日饮食和运动计划
            </p>
          </Link>

          <Link
            to="/timer"
            className="bg-white rounded-xl shadow-lg p-6 md:p-8 hover:shadow-xl transition-all hover:scale-105 active:scale-95"
          >
            <div className="text-3xl md:text-4xl mb-3 md:mb-4">⏱️</div>
            <h2 className="text-xl md:text-2xl font-bold text-gray-900 mb-2">运动计时</h2>
            <p className="text-sm md:text-base text-gray-600">
              使用正计时或倒计时记录你的运动时长
            </p>
          </Link>

          <Link
            to="/upload"
            className="bg-white rounded-xl shadow-lg p-6 md:p-8 hover:shadow-xl transition-all hover:scale-105 active:scale-95"
          >
            <div className="text-3xl md:text-4xl mb-3 md:mb-4">📤</div>
            <h2 className="text-xl md:text-2xl font-bold text-gray-900 mb-2">导入数据</h2>
            <p className="text-sm md:text-base text-gray-600">
              上传 Excel 或 PDF 文件快速导入计划数据
            </p>
          </Link>

          <Link
            to="/preferences"
            className="bg-white rounded-xl shadow-lg p-6 md:p-8 hover:shadow-xl transition-all hover:scale-105 active:scale-95"
          >
            <div className="text-3xl md:text-4xl mb-3 md:mb-4">⚙️</div>
            <h2 className="text-xl md:text-2xl font-bold text-gray-900 mb-2">个人设置</h2>
            <p className="text-sm md:text-base text-gray-600">
              配置你的健身目标、饮食偏好和活动水平
            </p>
          </Link>

          <Link
            to="/ai-chat"
            className="bg-white rounded-xl shadow-lg p-6 md:p-8 hover:shadow-xl transition-all hover:scale-105 active:scale-95"
          >
            <div className="text-3xl md:text-4xl mb-3 md:mb-4">🤖</div>
            <h2 className="text-xl md:text-2xl font-bold text-gray-900 mb-2">AI 助手</h2>
            <p className="text-sm md:text-base text-gray-600">
              让 AI 帮你生成个性化的饮食和运动计划
            </p>
          </Link>

          <Link
            to="/history"
            className="bg-white rounded-xl shadow-lg p-6 md:p-8 hover:shadow-xl transition-all hover:scale-105 active:scale-95"
          >
            <div className="text-3xl md:text-4xl mb-3 md:mb-4">📊</div>
            <h2 className="text-xl md:text-2xl font-bold text-gray-900 mb-2">历史记录</h2>
            <p className="text-sm md:text-base text-gray-600">
              查看你的训练历史和统计数据
            </p>
          </Link>
        </div>
      </div>
    </div>
  )
}
