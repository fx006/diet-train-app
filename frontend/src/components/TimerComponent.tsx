import { useState } from 'react'
import { useTimer } from '../hooks/useTimer'
import { useCountdown } from '../hooks/useCountdown'

type TimerMode = 'stopwatch' | 'countdown'

interface TimerComponentProps {
  onComplete?: (duration: number) => void
}

export default function TimerComponent({ onComplete }: TimerComponentProps) {
  const [mode, setMode] = useState<TimerMode>('stopwatch')
  const [countdownMinutes, setCountdownMinutes] = useState(30)

  // 正计时器
  const timer = useTimer()

  // 倒计时器
  const countdown = useCountdown(countdownMinutes * 60)

  // 格式化时间显示
  const formatTime = (totalSeconds: number) => {
    const hours = Math.floor(totalSeconds / 3600)
    const minutes = Math.floor((totalSeconds % 3600) / 60)
    const seconds = totalSeconds % 60

    if (hours > 0) {
      return `${hours.toString().padStart(2, '0')}:${minutes
        .toString()
        .padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
    }
    return `${minutes.toString().padStart(2, '0')}:${seconds
      .toString()
      .padStart(2, '0')}`
  }

  const handleComplete = () => {
    const duration = mode === 'stopwatch' ? timer.seconds : countdownMinutes * 60
    onComplete?.(Math.floor(duration / 60))
  }

  // 播放提示音
  const playNotificationSound = () => {
    // 创建简单的提示音
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
    const oscillator = audioContext.createOscillator()
    const gainNode = audioContext.createGain()

    oscillator.connect(gainNode)
    gainNode.connect(audioContext.destination)

    oscillator.frequency.value = 800
    oscillator.type = 'sine'

    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime)
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5)

    oscillator.start(audioContext.currentTime)
    oscillator.stop(audioContext.currentTime + 0.5)
  }

  // 倒计时完成时播放提示音
  if (countdown.isFinished && mode === 'countdown') {
    playNotificationSound()
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      {/* 模式切换 */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setMode('stopwatch')}
          className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${
            mode === 'stopwatch'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          正计时
        </button>
        <button
          onClick={() => setMode('countdown')}
          className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${
            mode === 'countdown'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          倒计时
        </button>
      </div>

      {/* 正计时器 */}
      {mode === 'stopwatch' && (
        <div className="text-center">
          <div className="text-6xl font-bold text-gray-900 mb-8 font-mono">
            {formatTime(timer.seconds)}
          </div>

          <div className="flex gap-3 justify-center">
            {!timer.isRunning && timer.seconds === 0 && (
              <button
                onClick={timer.start}
                className="px-8 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium"
              >
                开始
              </button>
            )}

            {timer.isRunning && (
              <button
                onClick={timer.pause}
                className="px-8 py-3 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 font-medium"
              >
                暂停
              </button>
            )}

            {!timer.isRunning && timer.seconds > 0 && (
              <>
                <button
                  onClick={timer.resume}
                  className="px-8 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium"
                >
                  继续
                </button>
                <button
                  onClick={timer.reset}
                  className="px-8 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 font-medium"
                >
                  重置
                </button>
              </>
            )}

            {timer.seconds > 0 && (
              <button
                onClick={handleComplete}
                className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
              >
                完成
              </button>
            )}
          </div>
        </div>
      )}

      {/* 倒计时器 */}
      {mode === 'countdown' && (
        <div className="text-center">
          {/* 时长设置 */}
          {!countdown.isRunning && countdown.seconds === countdownMinutes * 60 && (
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                设置时长（分钟）
              </label>
              <input
                type="number"
                min="1"
                max="180"
                value={countdownMinutes}
                onChange={(e) => {
                  const minutes = parseInt(e.target.value) || 1
                  setCountdownMinutes(minutes)
                  countdown.setTime(minutes * 60)
                }}
                className="w-32 px-3 py-2 border border-gray-300 rounded-lg text-center"
              />
            </div>
          )}

          <div
            className={`text-6xl font-bold mb-8 font-mono ${
              countdown.isFinished
                ? 'text-red-600 animate-pulse'
                : countdown.seconds <= 60
                ? 'text-orange-600'
                : 'text-gray-900'
            }`}
          >
            {formatTime(countdown.seconds)}
          </div>

          {countdown.isFinished && (
            <div className="mb-4 text-xl font-bold text-red-600">时间到！</div>
          )}

          <div className="flex gap-3 justify-center">
            {!countdown.isRunning && !countdown.isFinished && (
              <button
                onClick={countdown.start}
                className="px-8 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium"
              >
                开始
              </button>
            )}

            {countdown.isRunning && (
              <button
                onClick={countdown.pause}
                className="px-8 py-3 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 font-medium"
              >
                暂停
              </button>
            )}

            {!countdown.isRunning && countdown.seconds > 0 && countdown.seconds < countdownMinutes * 60 && (
              <button
                onClick={countdown.resume}
                className="px-8 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium"
              >
                继续
              </button>
            )}

            {countdown.seconds < countdownMinutes * 60 && (
              <button
                onClick={countdown.reset}
                className="px-8 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 font-medium"
              >
                重置
              </button>
            )}

            {countdown.isFinished && (
              <button
                onClick={handleComplete}
                className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
              >
                完成
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
