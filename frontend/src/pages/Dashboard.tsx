import { SearchMap } from '../components/map/SearchMap'
import { TelemetryPanel } from '../components/drone/TelemetryPanel'
import { DetectionAlert } from '../components/alerts/DetectionAlert'
import { CameraFeed } from '../components/drone/CameraFeed'
import { DroneController } from '../components/drone/DroneController'
import type { Detection, DroneTelemetry, WsMessage } from '../types'

interface DashboardProps {
  lastMessage: WsMessage | null
  isConnected: boolean
  telemetry: DroneTelemetry | null
  trail: Array<{ lat: number; lng: number }>
  mapDetections: Detection[]
  detectionCount: number
  onNewDetection: (detection: Detection) => void
}

export function Dashboard({
  isConnected,
  telemetry,
  trail,
  mapDetections,
  detectionCount,
  onNewDetection,
}: DashboardProps) {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '1fr 0.45fr 0.35fr',
      gridTemplateRows: '100vh',
      width: '100vw',
      height: '100vh',
      overflow: 'hidden',
      background: '#0A0E1A',
      gap: 6,
      padding: 6,
    }}>

      {/* ── Mapa — ocupa todo el alto ── */}
      <SearchMap
        telemetry={telemetry}
        detections={mapDetections}
        trail={trail}
      />

      {/* ── Panel misión: telemetría + cámara ── */}
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 6,
        minHeight: 0,
        overflowY: 'auto',
      }}>

        {/* Header */}
        <div style={{ color: 'white', fontFamily: 'monospace', padding: '4px 0' }}>
          <div style={{ fontSize: 16, fontWeight: 'bold', color: '#FF6D00' }}>
            AeroSearch AI
          </div>
          <div style={{ fontSize: 10, color: '#78909C' }}>
            Sistema de búsqueda y rescate
          </div>
        </div>

        {/* Telemetría */}
        <TelemetryPanel
          telemetry={telemetry}
          isConnected={isConnected}
          detectionCount={detectionCount}
        />

        {/* Cámara */}
        <CameraFeed onNewDetection={onNewDetection} />

      </div>

      {/* ── Panel alertas + control de vuelo ── */}
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 6,
        minHeight: 0,
        overflow: 'hidden',
      }}>

        {/* Alertas — ocupa el espacio disponible */}
        <div style={{ flex: 1, minHeight: 0 }}>
          <DetectionAlert detections={mapDetections} />
        </div>

        {/* Control de vuelo — tamaño fijo abajo */}
        <DroneController />

      </div>

    </div>
  )
}
