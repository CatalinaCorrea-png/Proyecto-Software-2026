import type { Detection } from '../../types'

interface Props {
  detections: Detection[]
}

export function DetectionAlert({ detections }: Props) {
  return (
    <div style={{
      background: '#0D1B2A',
      border: '1px solid #1E3A5F',
      borderRadius: '8px',
      padding: '12px',
      display: 'flex',
      flexDirection: 'column',
      gap: 8,
      height: '90vh',
      minHeight: 0,
      overflow: 'hidden'
    }}>
      <div style={{ fontSize: 11, color: '#78909C', fontFamily: 'monospace' }}>
        DETECCIONES RECIENTES
        {detections.length > 0 && (
          <span style={{
            marginLeft: 8, background: '#1E3A5F',
            color: '#00BCD4', fontSize: 10,
            padding: '1px 6px', borderRadius: 10
          }}>
            {detections.length}
          </span>
        )}
      </div>

      <div style={{ overflowY: 'auto', flex: 1 }}>
        {detections.length === 0 ? (
          <div style={{ color: '#1E3A5F', fontSize: 11, fontFamily: 'monospace' }}>
            sin detecciones
          </div>
        ) : (
          detections.map(det => {
            const color = det.confidence === 'high' ? '#00C853'
              : det.confidence === 'medium' ? '#FFD600'
              : '#FF5252'
            return (
              <div key={det.id} style={{
                display: 'grid',
                gridTemplateColumns: '8px 1fr auto',
                alignItems: 'center',
                gap: 8,
                padding: '8px 4px',
                borderBottom: '1px solid #0D1B2A',
              }}>
                {/* Indicador */}
                <div style={{
                  width: 8, height: 8, borderRadius: '50%',
                  background: color,
                  boxShadow: `0 0 4px ${color}`
                }} />

                {/* Info */}
                <div>
                  <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                    <span style={{
                      fontFamily: 'monospace', fontSize: 12,
                      fontWeight: 'bold', color
                    }}>
                      {det.confidence.toUpperCase()}
                    </span>
                    <span style={{
                      fontFamily: 'monospace', fontSize: 10,
                      color: '#78909C',
                      background: '#0A1520',
                      padding: '1px 5px', borderRadius: 3
                    }}>
                      {det.source}
                    </span>
                    {det.temperature && (
                      <span style={{
                        fontFamily: 'monospace', fontSize: 10,
                        color: '#FF6D00'
                      }}>
                        {det.temperature.toFixed(1)}°C
                      </span>
                    )}
                  </div>
                  <div style={{
                    fontFamily: 'monospace', fontSize: 10, color: '#455A64',
                    marginTop: 2
                  }}>
                    {det.position.lat.toFixed(5)}, {det.position.lng.toFixed(5)}
                  </div>
                </div>

                {/* Hora */}
                <div style={{
                  fontFamily: 'monospace', fontSize: 10, color: '#455A64'
                }}>
                  {new Date(det.timestamp).toLocaleTimeString()}
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}