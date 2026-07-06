import { useState, useCallback, useEffect } from 'react'
import { API_URL, WS_URL } from './config'
import { apiFetch } from './api'
import { useAuth, buildGuestLink } from './contexts/AuthContext'
import { LoginPage } from './pages/LoginPage'
import { MissionSetup } from './pages/MissionSetup'
import { Dashboard } from './pages/Dashboard'
import { MissionsHistory } from './pages/MissionsHistory'
import GalleryPage from './pages/GalleryPage'
import { StatsDashboard } from './pages/StatsDashboard'
import { MissionFinishedModal } from './components/MissionFinishedModal'
import { useWebSocket } from './hooks/useWebSocket'
import { useMission } from './hooks/useMission'
import type { Detection } from './types'
import './App.css'

type View = 'setup' | 'dashboard' | 'history' | 'gallery' | 'stats'

const ADMIN_NAV: { key: View; label: string }[] = [
  { key: 'setup',     label: 'Nueva Misión' },
  { key: 'dashboard', label: 'Dashboard' },
  { key: 'history',   label: 'Historial' },
  { key: 'gallery',   label: 'Galería' },
  { key: 'stats',     label: 'Estadísticas' },
]

// Invitado / solo lectura: misión en vivo + galería guardada.
const VIEWER_NAV: { key: View; label: string }[] = [
  { key: 'dashboard', label: 'Dashboard' },
  { key: 'gallery',   label: 'Galería' },
]

const VIEWER_VIEWS: View[] = VIEWER_NAV.map(n => n.key)

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

// Botón del Administrador para generar/copiar el enlace de acceso en modo
// lectura (Feature: enlace compartible). El enlace entra directo como
// invitado (GUEST), sin token ni panel administrativo — ver AuthContext.
function GuestLinkButton() {
  const [copied, setCopied] = useState(false)

  const handleClick = async () => {
    const link = buildGuestLink()
    try {
      await navigator.clipboard.writeText(link)
    } catch {
      // Clipboard bloqueado (permisos/HTTP no seguro): fallback visible para copiar a mano.
      window.prompt('Copiá el enlace de acceso en modo lectura:', link)
    }
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <button
      onClick={handleClick}
      className="app-nav__btn--share"
      title="Genera un enlace de acceso de solo lectura para compartir"
    >
      <span aria-hidden="true">{copied ? '✓' : '🔗'}</span> {copied ? 'Enlace copiado' : 'Compartir enlace'}
    </button>
  )
}

function App() {
  const { user } = useAuth()

  // Show login page if not authenticated
  if (!user) return <LoginPage />

  return <AppShell />
}

function AppShell() {
  const { user, logout } = useAuth()
  const isAdmin = user?.role === 'ADMIN'

  const hasMission = sessionStorage.getItem('missionActive') === '1'
  const initialView: View = isAdmin ? (hasMission ? 'dashboard' : 'setup') : 'dashboard'
  const [view, setView] = useState<View>(initialView)
  const [missionStarted, setMissionStarted] = useState(hasMission)
  const [showConfirm, setShowConfirm] = useState(false)
  const [missionFinished, setMissionFinished] = useState(false)

  // La verdad de si hay misión en curso está en el server, no en sessionStorage
  // (que es por-ventana: un espectador en otra ventana no tiene el flag). Consultamos
  // siempre para que cualquier ventana/rol descubra la misión activa y conecte la telemetría.
  useEffect(() => {
    apiFetch(`${API_URL}/mission/active`)
      .then(r => r.json())
      .then((data: { active: boolean }) => {
        if (data.active) {
          sessionStorage.setItem('missionActive', '1')
          setMissionStarted(true)
          if (!isAdmin) setView('dashboard')
        } else {
          sessionStorage.removeItem('missionActive')
          setMissionStarted(false)
          setView(isAdmin ? 'setup' : 'dashboard')
        }
      })
      .catch(() => {
        sessionStorage.removeItem('missionActive')
        setMissionStarted(false)
        setView(isAdmin ? 'setup' : 'dashboard')
      })
  }, [])  // eslint-disable-line react-hooks/exhaustive-deps

  const wsUrl = missionStarted ? `${WS_URL}/ws/mission` : null
  const { lastMessage, isConnected } = useWebSocket(wsUrl)
  const { telemetry, trail } = useMission(lastMessage)
  const [mapDetections, setMapDetections] = useState<Detection[]>([])
  const [detectionCount, setDetectionCount] = useState(0)

  // Invitados y usuarios en modo lectura: al finalizar la misión, cortamos la
  // conexión en tiempo real (missionStarted=false cierra el WS) y avisamos con
  // el modal. El admin ya sabe que la finalizó (la acción fue suya).
  useEffect(() => {
    if (lastMessage?.type === 'mission_finished' && !isAdmin) {
      setMissionFinished(true)
      setMissionStarted(false)
      sessionStorage.removeItem('missionActive')
    }
  }, [lastMessage, isAdmin])

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

  const handleNewMission = useCallback(async () => {
    if (missionStarted) {
      try {
        await apiFetch(`${API_URL}/mission/stop`, { method: 'POST' })
      } catch { /* backend down */ }
    }
    setMissionStarted(false)
    sessionStorage.removeItem('missionActive')
    setMapDetections([])
    setDetectionCount(0)
    setShowConfirm(false)
    setView('setup')
  }, [missionStarted])

  const handleStopMission = useCallback(async () => {
    try {
      await apiFetch(`${API_URL}/mission/stop`, { method: 'POST' })
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
    if (!isAdmin && !VIEWER_VIEWS.includes(key)) return
    if (key === 'dashboard' && !missionStarted && isAdmin) return
    setView(key)
  }

  const navItems = isAdmin ? ADMIN_NAV : VIEWER_NAV

  return (
    <div className="app">
      {showConfirm && (
        <ConfirmModal
          onConfirm={handleNewMission}
          onCancel={() => setShowConfirm(false)}
        />
      )}
      {missionFinished && (
        <MissionFinishedModal onClose={() => setMissionFinished(false)} />
      )}
      <nav className="app-nav">
        <span className="app-nav__brand">AeroSearch AI</span>
        {navItems.map(({ key, label }) => {
          const disabled = isAdmin && key === 'dashboard' && !missionStarted
          return (
            <button
              key={key}
              onClick={() => {
                if (isAdmin && key === 'setup' && missionStarted) {
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
        <div className="app-nav__actions">
          {isAdmin && (
            <>
              <GuestLinkButton />
              <span className="app-nav__divider" aria-hidden="true" />
            </>
          )}
          {isAdmin && missionStarted && (
            <>
              <button
                onClick={handleStopMission}
                className="app-nav__btn--stop"
                title="Finaliza la misión en curso y guarda sus datos"
              >
                <span aria-hidden="true">⏹</span> Finalizar Misión
              </button>
              <span className="app-nav__divider" aria-hidden="true" />
            </>
          )}
          <div className="app-nav__user">
            <span className="app-nav__username">{user?.username}</span>
            <span className="app-nav__role">{user?.role === 'GUEST' ? 'INVITADO' : user?.role}</span>
            <button onClick={logout} className="app-nav__logout">
              Salir
            </button>
          </div>
        </div>
      </nav>

      <div className="app-content">
        {isAdmin && view === 'setup' && (
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
        {isAdmin && view === 'history' && <MissionsHistory onViewGallery={handleViewGallery} />}
        {view === 'gallery' && (
          <div className="app-view app-content--scrollable">
            <GalleryPage initialMissionFilter={galleryMissionFilter} />
          </div>
        )}
        {isAdmin && view === 'stats' && (
          <div className="app-view app-content--scrollable">
            <StatsDashboard />
          </div>
        )}
        {!isAdmin && !VIEWER_VIEWS.includes(view) && (
          <div className="access-denied">
            <div className="access-denied__icon">⛔</div>
            <div className="access-denied__title">Acceso Denegado</div>
            <div className="access-denied__msg">
              El modo <strong>invitado</strong> solo tiene acceso al Dashboard y la Galería.
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
