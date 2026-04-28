import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Dashboard } from './pages/Dashboard'
import { DetectionsHistory } from './pages/DetectionHistory'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/history" element={<DetectionsHistory />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App