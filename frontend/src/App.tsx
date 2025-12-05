import { BrowserRouter, Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import DailyPlanView from './pages/DailyPlanView'
import TimerPage from './pages/TimerPage'
import FileUploadPage from './pages/FileUploadPage'
import PreferencesPage from './pages/PreferencesPage'
import AIChatPage from './pages/AIChatPage'
import HistoryPage from './pages/HistoryPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/plans" element={<DailyPlanView />} />
        <Route path="/timer" element={<TimerPage />} />
        <Route path="/upload" element={<FileUploadPage />} />
        <Route path="/preferences" element={<PreferencesPage />} />
        <Route path="/ai-chat" element={<AIChatPage />} />
        <Route path="/history" element={<HistoryPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
