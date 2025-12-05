import { useState, useEffect, useRef } from 'react'

export function useCountdown(initialSeconds: number = 0) {
  const [seconds, setSeconds] = useState(initialSeconds)
  const [isRunning, setIsRunning] = useState(false)
  const [isFinished, setIsFinished] = useState(false)
  const intervalRef = useRef<number | null>(null)

  useEffect(() => {
    if (isRunning && seconds > 0) {
      intervalRef.current = window.setInterval(() => {
        setSeconds((prev) => {
          if (prev <= 1) {
            setIsRunning(false)
            setIsFinished(true)
            return 0
          }
          return prev - 1
        })
      }, 1000)
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [isRunning, seconds])

  const start = () => {
    if (seconds > 0) {
      setIsRunning(true)
      setIsFinished(false)
    }
  }

  const pause = () => {
    setIsRunning(false)
  }

  const reset = () => {
    setIsRunning(false)
    setSeconds(initialSeconds)
    setIsFinished(false)
  }

  const resume = () => {
    if (seconds > 0) {
      setIsRunning(true)
    }
  }

  const setTime = (newSeconds: number) => {
    setSeconds(newSeconds)
    setIsFinished(false)
  }

  return {
    seconds,
    isRunning,
    isFinished,
    start,
    pause,
    reset,
    resume,
    setTime
  }
}
