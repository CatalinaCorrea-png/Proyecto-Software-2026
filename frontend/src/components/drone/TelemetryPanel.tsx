import type { DroneTelemetry } from '../../types'

interface Props {
  telemetry: DroneTelemetry | null
  isConnected: boolean
  detectionCount: number
}

export function TelemetryPanel({ telemetry, isConnected, detectionCount }: Props) {
  const batteryColor = !telemetry ? '#78909C'
    : telemetry.battery > 50 ? '#00C853'
    : telemetry.battery > 20 ? '#FFD600'
    : '#FF5252'

  return (
    <div style={{
      background: '#0D1B2A',
      border: '1px solid #1E3A5F',
      borderRadius: '8px',
      padding: '16px',
      color: 'white',
      fontFamily: 'monospace'
    }}>
      {/* Conexión */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
        <div style={{
          width: 10, height: 10, borderRadius: '50%',
          background: isConnected ? '#00C853' : '#FF5252',
          boxShadow: `0 0 6px ${isConnected ? '#00C853' : '#FF5252'}`
        }} />
        <span style={{ fontSize: 12, color: '#78909C' }}>
          {isConnected ? 'CONECTADO' : 'DESCONECTADO'}
        </span>
      </div>

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <Stat label="BATERÍA" value={telemetry ? `${telemetry.battery}%` : '--'} color={batteryColor} />
        <Stat label="ALTITUD" value={telemetry ? `${telemetry.position.altitude}m` : '--'} />
        <Stat label="VELOCIDAD" value={telemetry ? `${telemetry.speed} m/s` : '--'} />
        <Stat label="ESTADO" value={telemetry?.status ?? '--'} />
        <Stat label="DETECCIONES" value={String(detectionCount)} color="#FF6D00" />
        <Stat label="LAT" value={telemetry ? telemetry.position.lat.toFixed(5) : '--'} />
      </div>
    </div>
  )
}

function Stat({ label, value, color = '#E0E8F0' }: { label: string; value: string; color?: string }) {
  return (
    <div>
      <div style={{ fontSize: 10, color: '#78909C', marginBottom: 2 }}>{label}</div>
      <div style={{ fontSize: 16, fontWeight: 'bold', color }}>{value}</div>
    </div>
  )
}