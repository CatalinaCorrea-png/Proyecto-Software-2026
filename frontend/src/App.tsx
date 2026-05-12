import { useState, useCallback } from 'react'
import { Dashboard } from './pages/Dashboard'
import { MissionsHistory } from './pages/MissionsHistory'
import GalleryPage from './pages/GalleryPage'
import { useWebSocket } from './hooks/useWebSocket'
import { useMission } from './hooks/useMission'
import type { Detection } from './types'
import './App.css'

type View = 'dashboard' | 'history' | 'gallery'

function App() {
  const [view, setView] = useState<View>('dashboard')

  const { lastMessage, isConnected } = useWebSocket('ws://localhost:8000/ws/mission')
  const { telemetry, trail } = useMission(lastMessage)
  const [mapDetections, setMapDetections] = useState<Detection[]>([])

  const handleNewDetection = useCallback((detection: Detection) => {
    if (detection.confidence === 'low') return
    setMapDetections(prev => [detection, ...prev].slice(0, 10))
  }, [])

  const [galleryMissionFilter, setGalleryMissionFilter] = useState('')

  const handleViewGallery = useCallback((missionId: string) => {
    setGalleryMissionFilter(missionId)
    setView('gallery')
  }, [])

  const labels: Record<View, string> = { dashboard: 'Dashboard', history: 'Historial', gallery: 'Galería' }

  return (
    <div className="app">
      <nav className="app-nav">
        <span className="app-nav__brand">AeroSearch AI</span>
        {(['dashboard', 'history', 'gallery'] as View[]).map(v => (
          <button
            key={v}
            onClick={() => setView(v)}
            className={`app-nav__btn${view === v ? ' app-nav__btn--active' : ''}`}
          >
            {labels[v]}
          </button>
        ))}
      </nav>

      <div className="app-content">
        {/* Dashboard siempre montado para mantener los WebSockets activos */}
        <div className={`app-view${view !== 'dashboard' ? ' app-view--hidden' : ''}`}>
          <Dashboard
            lastMessage={lastMessage}
            isConnected={isConnected}
            telemetry={telemetry}
            trail={trail}
            mapDetections={mapDetections}
            onNewDetection={handleNewDetection}
          />
        </div>
        {view === 'history' && <MissionsHistory onViewGallery={handleViewGallery} />}
        {view === 'gallery' && (
          <div className="app-view app-content--scrollable">
            <GalleryPage initialMissionFilter={galleryMissionFilter} />
          </div>
        )}
      </div>
    </div>
  )
}

export default App
