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
  onNewDetection: (detection: Detection) => void
}

export function Dashboard({
  isConnected,
  telemetry,
  trail,
  mapDetections,
  onNewDetection,
}: DashboardProps) {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '1fr .5fr .5fr',
      gridTemplateRows: '1fr',
      width: '100%',
      height: '100%',
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
        <CameraFeed onNewDetection={onNewDetection} />

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
      }}>
        <DetectionAlert detections={mapDetections} />
      </div>

    </div>
  )
}
