import { useCallback, useEffect, useRef, useState } from 'react'
import { SearchMap } from '../components/map/SearchMap'
import { TelemetryPanel } from '../components/drone/TelemetryPanel'
import { DetectionAlert } from '../components/alerts/DetectionAlert'
import { CameraFeed } from '../components/drone/CameraFeed'
import { useWebSocket } from '../hooks/useWebSocket'
import { useMission } from '../hooks/useMission'
import type { Detection } from '../types'
import { type Metrics, PerformancePanel } from '../components/drone/PerformancePanel'
import { useDetectionFeed } from '../hooks/useDetectionFeed'

type MainView = 'map' | 'camera'

export function Dashboard() {
  // ── WebSocket de misión —────────
  const { lastMessage, isConnected } = useWebSocket('ws://localhost:8000/ws/mission')
  const { telemetry, trail } = useMission(lastMessage)

  // ── WebSocket de detección —────────
  const { framePayload, detections, isConnected: camConnected } = useDetectionFeed('ws://localhost:8000/ws/detection')
  const [mapDetections, setMapDetections] = useState<Detection[]>([])
  const [mainView, setMainView] = useState<MainView>('map')
  const lastDetectionRef = useRef<string | null>(null)
  // const [perfMetrics, setPerfMetrics] = useState<Metrics | null>(null)

  // Procesar deteccione
  useEffect(() => {
    if (detections.length === 0) return
    const latest = detections[0]
    if (latest.id === lastDetectionRef.current) return
    lastDetectionRef.current = latest.id
    if (latest.confidence === 'low') return
    setMapDetections(prev => [latest, ...prev].slice(0, 10))
  }, [detections])

  // const handleMetricsUpdate = useCallback((metrics: Metrics) => {
  //   setPerfMetrics(metrics)
  // }, [])

  const isMapMain = mainView === 'map'

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '1fr .5fr .5fr',
      gridTemplateRows: '100vh',
      width: '100vw',
      height: '100vh',
      background: '#070E18',
      gap: 8,
      padding: 8,
      boxSizing: 'border-box',
      fontFamily: 'monospace',
    }}>

      {/* ── Vista principal ── */}
      <div style={{
        flex: 1,
        borderRadius: 10,
        overflow: 'hidden',
        border: '1px solid #1A2E45',
        position: 'relative',
        transition: 'all 0.3s ease',
      }}>
        {isMapMain ? (
          <SearchMap
            telemetry={telemetry}
            detections={mapDetections}
            trail={trail}
          />
        ) : (
          <CameraFeed
            framePayload={framePayload}
            isConnected={camConnected}
            expanded
          />
        )}
      </div>

      {/* ── Panel derecho ── */}
      <div style={{
        // width: 300,
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
      }}>

        {/* Header */}
        <div style={{
          background: '#0D1B2A',
          border: '1px solid #1A2E45',
          borderRadius: 10,
          padding: '12px 14px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <div>
            <div style={{ fontSize: 16, fontWeight: 'bold', color: '#FF6D00', letterSpacing: 1 }}>
              AeroSearch AI
            </div>
            <div style={{ fontSize: 9, color: '#455A64', letterSpacing: 2, marginTop: 2 }}>
              BÚSQUEDA Y RESCATE
            </div>
          </div>

          {/* Toggle switch */}
          <ViewToggle
            isMapMain={isMapMain}
            onToggle={() => setMainView(v => v === 'map' ? 'camera' : 'map')}
          />
        </div>

        {/* Telemetría */}
        <TelemetryPanel
          telemetry={telemetry}
          isConnected={isConnected}
          detectionCount={mapDetections.length}
        />

        {/* Vista secundaria */}
        <div style={{
          borderRadius: 10,
          overflow: 'hidden',
          border: '1px solid #1A2E45',
          position: 'relative',
          flexShrink: 0,
        }}>
          {isMapMain ? (
            <CameraFeed 
              framePayload={framePayload}
              isConnected={camConnected}
            />
          ) : (
            <div style={{ height: 400 }}>
              <SearchMap
                telemetry={telemetry}
                detections={mapDetections}
                trail={trail}
              />
            </div>
          )}
        </div>
      </div>

      <div style={{
      // width: 300,
      display: 'flex',
      flexDirection: 'column',
      gap: 8,
      }}>
        {/* Alertas */}
        <PerformancePanel metrics={framePayload?.metrics ?? null} />
        <DetectionAlert detections={mapDetections} />
      </div>

    </div>
  )
}

// ── Toggle component ──────────────────────────────────────────────────────────
interface ViewToggleProps {
  isMapMain: boolean
  onToggle: () => void
}

function ViewToggle({ isMapMain, onToggle }: ViewToggleProps) {
  return (
    <button
      onClick={onToggle}
      title={isMapMain ? 'Poner cámara en principal' : 'Poner mapa en principal'}
      style={{
        background: 'transparent',
        border: '1px solid #1A2E45',
        borderRadius: 8,
        padding: '6px 8px',
        cursor: 'pointer',
        display: 'flex',
        alignItems: 'center',
        gap: 6,
        transition: 'border-color 0.2s, background 0.2s',
      }}
      onMouseEnter={e => {
        (e.currentTarget as HTMLButtonElement).style.borderColor = '#00BCD4'
        ;(e.currentTarget as HTMLButtonElement).style.background = 'rgba(0,188,212,0.06)'
      }}
      onMouseLeave={e => {
        (e.currentTarget as HTMLButtonElement).style.borderColor = '#1A2E45'
        ;(e.currentTarget as HTMLButtonElement).style.background = 'transparent'
      }}
    >
      {/* Ícono mapa */}
      <span style={{
        fontSize: 13,
        opacity: isMapMain ? 1 : 0.35,
        transition: 'opacity 0.2s'
      }}>
        🗺️
      </span>

      {/* Track del switch */}
      <div style={{
        width: 28,
        height: 14,
        background: '#1A2E45',
        borderRadius: 7,
        position: 'relative',
      }}>
        <div style={{
          position: 'absolute',
          top: 2,
          left: isMapMain ? 2 : 14,
          width: 10,
          height: 10,
          borderRadius: '50%',
          background: '#00BCD4',
          transition: 'left 0.2s ease',
          boxShadow: '0 0 6px #00BCD4',
        }} />
      </div>

      {/* Ícono cámara */}
      <span style={{
        fontSize: 13,
        opacity: isMapMain ? 0.35 : 1,
        transition: 'opacity 0.2s'
      }}>
        📷
      </span>
    </button>
  )
}