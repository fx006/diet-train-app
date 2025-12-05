import { useNavigate } from 'react-router-dom'
import FileUploader from '../components/FileUploader'

export default function FileUploadPage() {
  const navigate = useNavigate()

  const handleSuccess = () => {
    // 上传成功后可以跳转到计划页面
    setTimeout(() => {
      navigate('/plans')
    }, 2000)
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
        <h1 className="text-3xl font-bold text-gray-900 mb-6">导入计划数据</h1>

        {/* 文件上传组件 */}
        <FileUploader onSuccess={handleSuccess} />

        {/* 示例文件说明 */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="font-semibold text-blue-900 mb-3">Excel 文件示例格式</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-blue-100">
                <tr>
                  <th className="px-3 py-2 text-left text-blue-900">日期</th>
                  <th className="px-3 py-2 text-left text-blue-900">类型</th>
                  <th className="px-3 py-2 text-left text-blue-900">名称</th>
                  <th className="px-3 py-2 text-left text-blue-900">热量</th>
                  <th className="px-3 py-2 text-left text-blue-900">时长</th>
                </tr>
              </thead>
              <tbody className="bg-white">
                <tr className="border-b border-blue-100">
                  <td className="px-3 py-2 text-gray-700">2024-01-01</td>
                  <td className="px-3 py-2 text-gray-700">餐食</td>
                  <td className="px-3 py-2 text-gray-700">早餐</td>
                  <td className="px-3 py-2 text-gray-700">500</td>
                  <td className="px-3 py-2 text-gray-700">-</td>
                </tr>
                <tr className="border-b border-blue-100">
                  <td className="px-3 py-2 text-gray-700">2024-01-01</td>
                  <td className="px-3 py-2 text-gray-700">运动</td>
                  <td className="px-3 py-2 text-gray-700">跑步</td>
                  <td className="px-3 py-2 text-gray-700">300</td>
                  <td className="px-3 py-2 text-gray-700">30</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}
