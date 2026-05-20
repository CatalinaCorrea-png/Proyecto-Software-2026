import { useState, useCallback, useEffect } from 'react'
import { MissionSetup } from './pages/MissionSetup'
import { Dashboard } from './pages/Dashboard'
import { MissionsHistory } from './pages/MissionsHistory'
import GalleryPage from './pages/GalleryPage'
import { useWebSocket } from './hooks/useWebSocket'
import { useMission } from './hooks/useMission'
import type { Detection } from './types'
import './App.css'

type View = 'setup' | 'dashboard' | 'history' | 'gallery'

function ConfirmModal({ onConfirm, onCancel }: { onConfirm: () => void; onCancel: () => void }) {
  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 9999,
      background: 'rgba(0,0,0,0.6)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
    }} onClick={onCancel}>
      <div
        onClick={e => e.stopPropagation()}
        style={{
          background: '#0D1B2A', border: '1px solid #1E3A5F',
          borderRadius: 8, padding: '24px 28px', width: 360,
          fontFamily: 'monospace', color: '#E0E0E0',
          display: 'flex', flexDirection: 'column', gap: 16,
        }}
      >
        <div style={{ fontSize: 14, fontWeight: 'bold', color: '#FFC107' }}>
          Finalizar misión actual
        </div>
        <div style={{ fontSize: 12, color: '#90A4AE', lineHeight: 1.5 }}>
          Se finalizará la misión en curso y se guardarán sus datos.
          Esta acción no se puede deshacer.
        </div>
        <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
          <button
            onClick={onCancel}
            style={{
              background: 'transparent', border: '1px solid #37474F',
              borderRadius: 4, padding: '6px 16px', color: '#78909C',
              fontFamily: 'monospace', fontSize: 11, cursor: 'pointer',
            }}
          >
            Cancelar
          </button>
          <button
            onClick={onConfirm}
            style={{
              background: '#FF6D00', border: 'none',
              borderRadius: 4, padding: '6px 16px', color: '#fff',
              fontFamily: 'monospace', fontSize: 11, fontWeight: 'bold',
              cursor: 'pointer',
            }}
          >
            Nueva misión
          </button>
        </div>
      </div>
    </div>
  )
}

function App() {
  const hasMission = sessionStorage.getItem('missionActive') === '1'
  const [view, setView] = useState<View>(hasMission ? 'dashboard' : 'setup')
  const [missionStarted, setMissionStarted] = useState(hasMission)
  const [showConfirm, setShowConfirm] = useState(false)

  useEffect(() => {
    if (!hasMission) return
    fetch('http://localhost:8000/mission/active')
      .then(r => r.json())
      .then(data => {
        if (!data.active) {
          sessionStorage.removeItem('missionActive')
          setMissionStarted(false)
          setView('setup')
        }
      })
      .catch(() => {
        sessionStorage.removeItem('missionActive')
        setMissionStarted(false)
        setView('setup')
      })
  }, [])  // eslint-disable-line react-hooks/exhaustive-deps

  const wsUrl = missionStarted ? 'ws://localhost:8000/ws/mission' : null
  const { lastMessage, isConnected } = useWebSocket(wsUrl)
  const { telemetry, trail } = useMission(lastMessage)
  const [mapDetections, setMapDetections] = useState<Detection[]>([])
  const [detectionCount, setDetectionCount] = useState(0)

  const handleNewDetection = useCallback((detection: Detection) => {
    if (detection.confidence === 'low') return
    setDetectionCount(c => c + 1)
    setMapDetections(prev => [detection, ...prev].slice(0, 10))
  }, [])

  const handleMissionStart = useCallback(() => {
    setMapDetections([])
    setDetectionCount(0)
    setMissionStarted(true)
    sessionStorage.setItem('missionActive', '1')
    setView('dashboard')
  }, [])

  const handleNewMission = useCallback(() => {
    setMissionStarted(false)
    sessionStorage.removeItem('missionActive')
    setMapDetections([])
    setDetectionCount(0)
    setShowConfirm(false)
    setView('setup')
  }, [])

  const handleStopMission = useCallback(async () => {
    try {
      await fetch('http://localhost:8000/mission/stop', { method: 'POST' })
    } catch { /* backend down */ }
    setMissionStarted(false)
    sessionStorage.removeItem('missionActive')
    setView('setup')
  }, [])

  const [galleryMissionFilter, setGalleryMissionFilter] = useState('')

  const handleViewGallery = useCallback((missionId: string) => {
    setGalleryMissionFilter(missionId)
    setView('gallery')
  }, [])

  const handleNavClick = (key: View) => {
    if (key === 'dashboard' && !missionStarted) return
    setView(key)
  }

  const navItems: { key: View; label: string }[] = [
    { key: 'setup', label: 'Nueva Misión' },
    { key: 'dashboard', label: 'Dashboard' },
    { key: 'history', label: 'Historial' },
    { key: 'gallery', label: 'Galería' },
  ]

  return (
    <div className="app">
      {showConfirm && (
        <ConfirmModal
          onConfirm={handleNewMission}
          onCancel={() => setShowConfirm(false)}
        />
      )}
      <nav className="app-nav">
        <span className="app-nav__brand">AeroSearch AI</span>
        {navItems.map(({ key, label }) => {
          const disabled = key === 'dashboard' && !missionStarted
          return (
            <button
              key={key}
              onClick={() => {
                if (key === 'setup' && missionStarted) {
                  setShowConfirm(true)
                } else {
                  handleNavClick(key)
                }
              }}
              disabled={disabled}
              className={`app-nav__btn${view === key ? ' app-nav__btn--active' : ''}${disabled ? ' app-nav__btn--disabled' : ''}`}
            >
              {label}
            </button>
          )
        })}
        {missionStarted && (
          <button
            onClick={handleStopMission}
            className="app-nav__btn app-nav__btn--stop"
          >
            Finalizar Misión
          </button>
        )}
      </nav>

      <div className="app-content">
        {view === 'setup' && (
          <MissionSetup onStart={handleMissionStart} />
        )}
        <div className={`app-view${view !== 'dashboard' ? ' app-view--hidden' : ''}`}>
          <Dashboard
            lastMessage={lastMessage}
            isConnected={isConnected}
            telemetry={telemetry}
            trail={trail}
            mapDetections={mapDetections}
            detectionCount={detectionCount}
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
