import { useRef } from 'react'
import type { DroneTelemetry } from '../../types'

interface Props {
  telemetry: DroneTelemetry | null
  isConnected: boolean
  detectionCount: number
}

function formatElapsed(seconds: number | undefined): string {
  if (seconds === undefined || isNaN(seconds)) return '--:--'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  if (h > 0) return `${h}h ${m.toString().padStart(2, '0')}m`
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

export function TelemetryPanel({ telemetry, isConnected, detectionCount }: Props) {
  const batteryColor = !telemetry ? '#78909C'
    : telemetry.battery > 50 ? '#00C853'
    : telemetry.battery > 20 ? '#FFD600'
    : '#FF5252'

  // Guardar último elapsed válido para no parpadear
  const lastElapsedRef = useRef<number>(0)
  if (telemetry?.elapsed !== undefined) {
    lastElapsedRef.current = telemetry.elapsed
  }

  return (
    <div style={{
      background: '#0D1B2A',
      border: '1px solid #1E3A5F',
      borderRadius: '8px',
      padding: '16px',
      color: 'white',
      fontFamily: 'monospace'
    }}>
      {/* Conexión + fuente de datos */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
        <div style={{
          width: 10, height: 10, borderRadius: '50%',
          background: isConnected ? '#00C853' : '#FF5252',
          boxShadow: `0 0 6px ${isConnected ? '#00C853' : '#FF5252'}`
        }} />
        <span style={{ fontSize: 12, color: '#78909C' }}>
          {isConnected ? 'CONECTADO' : 'DESCONECTADO'}
        </span>
        <span style={{
          marginLeft: 'auto',
          fontSize: 9, fontWeight: 'bold', letterSpacing: 1,
          padding: '2px 6px', borderRadius: 3,
          background: telemetry?.source === 'hardware' ? '#00C85320'
            : telemetry?.source === 'manual' ? '#FF6D0020' : '#1E3A5F',
          color: telemetry?.source === 'hardware' ? '#00C853'
            : telemetry?.source === 'manual' ? '#FF6D00' : '#546E7A',
          border: `1px solid ${telemetry?.source === 'hardware' ? '#00C85360'
            : telemetry?.source === 'manual' ? '#FF6D0060' : '#1E3A5F'}`,
        }}>
          {telemetry?.source === 'hardware' ? 'HW LIVE'
            : telemetry?.source === 'manual' ? 'MANUAL' : 'SIMULADO'}
        </span>
      </div>

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
        <Stat label="BATERÍA" value={telemetry ? `${telemetry.battery}%` : '--'} color={batteryColor} />
        <Stat label="ALTITUD" value={telemetry ? `${telemetry.position.altitude}m` : '--'} />
        <Stat label="VELOCIDAD" value={telemetry ? `${telemetry.speed} m/s` : '--'} />
        <Stat label="ESTADO" value={telemetry?.status ?? '--'} />
        <Stat label="LAT" value={telemetry ? telemetry.position.lat.toFixed(5) : '--'} />
        <Stat label="LNG" value={telemetry ? telemetry.position.lng.toFixed(5) : '--'} />
        <Stat label="DETECCIONES" value={String(detectionCount)} color="#FF6D00" />
        <Stat label="MISIÓN" value={formatElapsed(lastElapsedRef.current)} color="#00BCD4"/>
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