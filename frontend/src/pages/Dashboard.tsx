import { useCallback, useState } from 'react'
import { SearchMap } from '../components/map/SearchMap'
import { TelemetryPanel } from '../components/drone/TelemetryPanel'
import { DetectionAlert } from '../components/alerts/DetectionAlert'
import { CameraFeed } from '../components/drone/CameraFeed'
import { DroneController } from '../components/drone/DroneController'
import { useWebSocket } from '../hooks/useWebSocket'
import { useMission } from '../hooks/useMission'
import type { Detection } from '../types'

export function Dashboard() {
  const { lastMessage, isConnected } = useWebSocket('ws://localhost:8000/ws/mission')
  const { telemetry, trail } = useMission(lastMessage)
  const [mapDetections, setMapDetections] = useState<Detection[]>([])

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

      {/* ── Panel telemetria, camara y control ── */}
      <div style={{
        display: 'grid',
        gridTemplateRows: 'auto auto auto auto',
        gap: 10,
        alignContent: 'start',
        overflowY: 'auto',
        minHeight: 0,
      }}>

        {/* Header */}
        <div style={{ color: 'white', fontFamily: 'monospace' }}>
          <div style={{ fontSize: 22, fontWeight: 'bold', color: '#FF6D00' }}>
            AeroSearch AI
          </div>
          <div style={{ fontSize: 11, color: '#78909C' }}>
            Sistema de búsqueda y rescate
          </div>
        </div>

        {/* Telemetría */}
        <TelemetryPanel
          telemetry={telemetry}
          isConnected={isConnected}
          detectionCount={mapDetections.length}
        />

        {/* Cámara */}
        <CameraFeed onNewDetection={handleNewDetection} />

        {/* Control de vuelo */}
        <DroneController />

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