import type { Detection } from '../../types'

interface Props {
  detections: Detection[]
}

export function DetectionAlert({ detections }: Props) {
  if (detections.length === 0) return null

  return (
    <div style={{
      background: '#0D1B2A',
      border: '1px solid #1E3A5F',
      borderRadius: '8px',
      padding: '12px',
      maxHeight: '220px',
      overflowY: 'auto'
    }}>
      <div style={{ fontSize: 11, color: '#78909C', marginBottom: 8, fontFamily: 'monospace' }}>
        DETECCIONES RECIENTES
      </div>
      {detections.map(det => { // map = por cada detección, creá un elemento
        const color = det.confidence === 'high' ? '#00C853'
          : det.confidence === 'medium' ? '#FFD600'
          : '#FF5252'
        return (
          <div key={det.id} style={{
            display: 'flex', alignItems: 'center', gap: 10,
            padding: '8px 0',
            borderBottom: '1px solid #1E3A5F',
            fontFamily: 'monospace'
          }}>
            <div style={{
              width: 8, height: 8, borderRadius: '50%',
              background: color, flexShrink: 0,
              boxShadow: `0 0 4px ${color}`
            }} />
            <div style={{ flex: 1 }}>
              <span style={{ color, fontSize: 12, fontWeight: 'bold' }}>
                {det.confidence.toUpperCase()}
              </span>
              <span style={{ color: '#78909C', fontSize: 11, marginLeft: 8 }}>
                {det.source} {det.temperature ? `· ${det.temperature}°C` : ''}
              </span>
            </div>
            <div style={{ color: '#78909C', fontSize: 11 }}>
              {new Date(det.timestamp).toLocaleTimeString()}
            </div>
          </div>
        )
      })}
    </div>
  )
}