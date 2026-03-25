import { SearchMap } from '../components/map/SearchMap'
import { TelemetryPanel } from '../components/drone/TelemetryPanel'
import { DetectionAlert } from '../components/alerts/DetectionAlert'
import { useWebSocket } from '../hooks/useWebSocket'
import { useMission } from '../hooks/useMission'

export function Dashboard() {
  // Acá viven los hooks — los datos fluyen de arriba hacia abajo
  const { lastMessage, isConnected } = useWebSocket('ws://localhost:8000/ws/mission')
  const { telemetry, detections, trail } = useMission(lastMessage)

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
      {/* Mapa principal */}
      {/* Le pasa los datos a cada hijo como props */}
      <SearchMap
        telemetry={telemetry}
        detections={detections}
        trail={trail}
      />

      {/* Panel derecho */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {/* Header */}
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
          detectionCount={detections.length}
        />

        <DetectionAlert detections={detections} />
      </div>
    </div>
  )
}