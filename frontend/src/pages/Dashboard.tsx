import { useCallback, useState } from 'react'
import { SearchMap } from '../components/map/SearchMap'
import { TelemetryPanel } from '../components/drone/TelemetryPanel'
import { DetectionAlert } from '../components/alerts/DetectionAlert'
import { CameraFeed } from '../components/drone/CameraFeed'
import { useWebSocket } from '../hooks/useWebSocket'
import { useMission } from '../hooks/useMission'
import type { Detection } from '../types'
import { useNavigate } from 'react-router-dom'

export function Dashboard() {
  const { lastMessage, isConnected } = useWebSocket('ws://localhost:8000/ws/mission')
  const { telemetry, trail } = useMission(lastMessage)
  const [mapDetections, setMapDetections] = useState<Detection[]>([])
  const navigate = useNavigate()

  const handleNewDetection = useCallback((detection: Detection) => {
    if (detection.confidence === 'low') return
    setMapDetections(prev => [detection, ...prev].slice(0, 10))
  }, [])

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '1fr .5fr .5fr',
      gridTemplateRows: '100vh',
      width: '100vw',
      height: '100vh',
      overflow: 'hidden',
      background: '#0A0E1A',
      gap: 10,
      padding: 10,
    }}>

      {/* ── Mapa — ocupa todo el alto ── */}
      <SearchMap
        telemetry={telemetry}
        detections={mapDetections}
        trail={trail}
      />

      {/* ── Panel telemetria y camara ── */}
      <div style={{
        display: 'grid',
        gridTemplateRows: 'auto auto auto',
        gap: 10,
        alignContent: 'center',
        overflowY: 'auto',
        minHeight: 0,
        // height: '100vh'
      }}>

        {/* Header */}
        <div style={{ color: 'white', fontFamily: 'monospace' }}>
          <div style={{ fontSize: 22, fontWeight: 'bold', color: '#FF6D00' }}>
            AeroSearch AI
          </div>
          <div style={{ fontSize: 11, color: '#78909C' }}>
            Sistema de búsqueda y rescate
          </div>
          <button
            onClick={() => navigate('/history')}
            style={{
              marginTop: 6, fontSize: 10, fontFamily: 'monospace',
              background: '#1E3A5F', color: '#00BCD4',
              border: 'none', borderRadius: 4, padding: '4px 10px',
              cursor: 'pointer',
            }}
          >
            VER HISTORIAL →
          </button>
        </div>

        {/* Telemetría */}
        <TelemetryPanel
          telemetry={telemetry}
          isConnected={isConnected}
          detectionCount={mapDetections.length}
        />

        {/* Cámara — sin panel de detecciones propio */}
        <CameraFeed onNewDetection={handleNewDetection} />

      </div>

      {/* ── Panel alertas ── */}
      <div style={{
        display: 'grid',
        gridTemplateRows: 'auto',
        gap: 10,
        alignContent: 'center',
        overflowY: 'auto',
        minHeight: 0,
        // height: '100vh'
      }}>

        {/* ──  Alertas — detecciones del mapa ── */}
        <DetectionAlert detections={mapDetections} />

      </div>


    </div>
  )
}