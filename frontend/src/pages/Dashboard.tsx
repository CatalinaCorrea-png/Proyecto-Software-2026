import { useCallback, useState } from 'react'
import { SearchMap } from '../components/map/SearchMap'
import { TelemetryPanel } from '../components/drone/TelemetryPanel'
import { DetectionAlert } from '../components/alerts/DetectionAlert'
import { CameraFeed } from '../components/drone/CameraFeed'
import { useWebSocket } from '../hooks/useWebSocket'
import { useMission } from '../hooks/useMission'
import type { Detection } from '../types'

export function Dashboard() {
  const { lastMessage, isConnected } = useWebSocket('ws://localhost:8000/ws/mission')
  const { telemetry, trail } = useMission(lastMessage)

  // ── NUEVO: detecciones reales del pipeline de IA ──────────────────────────
  const [mapDetections, setMapDetections] = useState<Detection[]>([])

  const handleNewDetection = useCallback((detection: Detection) => {
    setMapDetections(prev => [detection, ...prev].slice(0, 100))
  }, [])
  // ─────────────────────────────────────────────────────────────────────────

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '1fr 300px',
      gridTemplateRows: '100vh',
      background: '#0A0E1A',
      gap: 12,
      padding: 12,
      boxSizing: 'border-box'
    }}>
      {/* Mapa — ahora recibe detecciones reales */}
      <SearchMap
        telemetry={telemetry}
        detections={mapDetections}    // ← detecciones del pipeline
        trail={trail}
      />

      <div style={{
        display: 'flex', flexDirection: 'column', gap: 12,
        overflowY: 'auto'
      }}>
        <div style={{ color: 'white', fontFamily: 'monospace' }}>
          <div style={{ fontSize: 20, fontWeight: 'bold', color: '#FF6D00' }}>
            AeroSearch AI
          </div>
          <div style={{ fontSize: 11, color: '#78909C' }}>
            Sistema de búsqueda y rescate
          </div>
        </div>

        <TelemetryPanel
          telemetry={telemetry}
          isConnected={isConnected}
          detectionCount={mapDetections.length}
        />

        {/* CameraFeed avisa cuando detecta algo */}
        <CameraFeed onNewDetection={handleNewDetection} />

        <DetectionAlert detections={mapDetections} />
      </div>
    </div>
  )
}