import { useState, useRef } from 'react'
import { filesApi } from '../api/files'

interface FileUploaderProps {
  onSuccess?: () => void
}

export default function FileUploader({ onSuccess }: FileUploaderProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const acceptedTypes = [
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // .xlsx
    'application/vnd.ms-excel', // .xls
    'application/pdf'
  ]

  const acceptedExtensions = ['.xlsx', '.xls', '.pdf']

  const validateFile = (file: File): boolean => {
    // 检查文件类型
    if (!acceptedTypes.includes(file.type) && !acceptedExtensions.some(ext => file.name.toLowerCase().endsWith(ext))) {
      setError('只支持 Excel (.xlsx, .xls) 和 PDF 文件')
      return false
    }

    // 检查文件大小（最大10MB）
    if (file.size > 10 * 1024 * 1024) {
      setError('文件大小不能超过 10MB')
      return false
    }

    return true
  }

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile && validateFile(droppedFile)) {
      setFile(droppedFile)
      setError('')
      setSuccess(false)
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile && validateFile(selectedFile)) {
      setFile(selectedFile)
      setError('')
      setSuccess(false)
    }
  }

  const handleUpload = async () => {
    if (!file) return

    setUploading(true)
    setProgress(0)
    setError('')
    setSuccess(false)

    try {
      await filesApi.upload(file, setProgress)
      setSuccess(true)
      setFile(null)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
      onSuccess?.()
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail?.message || '上传失败，请重试'
      setError(errorMessage)
    } finally {
      setUploading(false)
      setProgress(0)
    }
  }

  const handleCancel = () => {
    setFile(null)
    setError('')
    setSuccess(false)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-4">上传文件</h2>

      {/* 拖拽区域 */}
      <div
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          isDragging
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
      >
        <div className="text-6xl mb-4">📁</div>
        <p className="text-lg font-medium text-gray-900 mb-2">
          拖拽文件到这里，或点击选择文件
        </p>
        <p className="text-sm text-gray-600 mb-4">
          支持 Excel (.xlsx, .xls) 和 PDF 文件，最大 10MB
        </p>

        <input
          ref={fileInputRef}
          type="file"
          accept=".xlsx,.xls,.pdf"
          onChange={handleFileSelect}
          className="hidden"
          id="file-input"
        />
        <label
          htmlFor="file-input"
          className="inline-block px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer"
        >
          选择文件
        </label>
      </div>

      {/* 选中的文件 */}
      {file && !uploading && !success && (
        <div className="mt-4 p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="text-2xl">
                {file.name.endsWith('.pdf') ? '📄' : '📊'}
              </div>
              <div>
                <p className="font-medium text-gray-900">{file.name}</p>
                <p className="text-sm text-gray-600">
                  {(file.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            </div>
            <button
              onClick={handleCancel}
              className="text-gray-500 hover:text-gray-700"
            >
              ✕
            </button>
          </div>

          <div className="flex gap-3 mt-4">
            <button
              onClick={handleUpload}
              className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
            >
              上传
            </button>
            <button
              onClick={handleCancel}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
            >
              取消
            </button>
          </div>
        </div>
      )}

      {/* 上传进度 */}
      {uploading && (
        <div className="mt-4 p-4 bg-blue-50 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-blue-900">上传中...</span>
            <span className="text-sm font-medium text-blue-900">{progress}%</span>
          </div>
          <div className="w-full bg-blue-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* 成功消息 */}
      {success && (
        <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center gap-2 text-green-800">
            <span className="text-2xl">✓</span>
            <span className="font-medium">上传成功！数据已导入。</span>
          </div>
        </div>
      )}

      {/* 错误消息 */}
      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center gap-2 text-red-800">
            <span className="text-2xl">⚠</span>
            <span className="font-medium">{error}</span>
          </div>
        </div>
      )}

      {/* 使用说明 */}
      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <h3 className="font-semibold text-gray-900 mb-2">文件格式要求</h3>
        <ul className="text-sm text-gray-700 space-y-1">
          <li>• Excel 文件应包含：日期、类型、名称、热量、时长等列</li>
          <li>• PDF 文件会自动识别表格数据</li>
          <li>• 确保日期格式为 YYYY-MM-DD</li>
          <li>• 类型应为"餐食"或"运动"</li>
        </ul>
      </div>
    </div>
  )
}
