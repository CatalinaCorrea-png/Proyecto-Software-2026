import { useState, useCallback } from 'react'
import { Dashboard } from './pages/Dashboard'
import GalleryPage from './pages/GalleryPage'
import { useWebSocket } from './hooks/useWebSocket'
import { useMission } from './hooks/useMission'
import type { Detection } from './types'
import './App.css'

type Page = 'dashboard' | 'gallery'

function App() {
  const [page, setPage] = useState<Page>('dashboard')

  // WebSocket de misión vive aquí para sobrevivir la navegación
  const { lastMessage, isConnected } = useWebSocket('ws://localhost:8000/ws/mission')
  const { telemetry, trail } = useMission(lastMessage)
  const [mapDetections, setMapDetections] = useState<Detection[]>([])

  const handleNewDetection = useCallback((detection: Detection) => {
    if (detection.confidence === 'low') return
    setMapDetections(prev => [detection, ...prev].slice(0, 10))
  }, [])

  return (
    <div className="app">
      <nav className="app-nav">
        <span className="app-nav__brand">AeroSearch AI</span>
        <button
          className={`app-nav__btn${page === 'dashboard' ? ' app-nav__btn--active' : ''}`}
          onClick={() => setPage('dashboard')}
        >
          Dashboard
        </button>
        <button
          className={`app-nav__btn${page === 'gallery' ? ' app-nav__btn--active' : ''}`}
          onClick={() => setPage('gallery')}
        >
          Galería
        </button>
      </nav>
      <div className={`app-content${page === 'gallery' ? ' app-content--scrollable' : ''}`}>
        {page === 'dashboard' ? (
          <Dashboard
            lastMessage={lastMessage}
            isConnected={isConnected}
            telemetry={telemetry}
            trail={trail}
            mapDetections={mapDetections}
            onNewDetection={handleNewDetection}
          />
        ) : (
          <GalleryPage />
        )}
      </div>
    </div>
  )
}

export default App
