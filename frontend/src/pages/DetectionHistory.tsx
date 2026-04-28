import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDetections } from '../hooks/useDetections'

const CONFIDENCE_COLOR = {
  high:   '#00C853',
  medium: '#FFD600',
  low:    '#FF5252',
}

export function DetectionsHistory() {
  const navigate = useNavigate()
  const { detections, loading, refetch } = useDetections()
  const [selected, setSelected] = useState<string | null>(null)

  const selectedDet = detections.find(d => d.id === selected)

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '380px 1fr',
      height: '100vh',
      background: '#0A0E1A',
      color: 'white',
      fontFamily: 'monospace',
    }}>

      {/* ── Lista izquierda ── */}
      <div style={{
        borderRight: '1px solid #1E3A5F',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}>
        {/* Header */}
        <div style={{
          padding: '16px',
          borderBottom: '1px solid #1E3A5F',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <div>
            <div style={{ fontSize: 18, fontWeight: 'bold', color: '#FF6D00' }}>
              Historial
            </div>
            <div style={{ fontSize: 11, color: '#78909C' }}>
              {detections.length} detecciones
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button onClick={refetch} style={btnStyle('#1E3A5F')}>↻ Refresh</button>
            <button onClick={() => navigate('/')} style={btnStyle('#1E3A5F')}>← Volver</button>
          </div>
        </div>

        {/* Cards */}
        <div style={{ overflowY: 'auto', flex: 1 }}>
          {loading && (
            <div style={{ padding: 24, color: '#78909C', textAlign: 'center' }}>
              Cargando...
            </div>
          )}
          {detections.map(det => (
            <div
              key={det.id}
              onClick={() => setSelected(det.id)}
              style={{
                padding: '12px 16px',
                borderBottom: '1px solid #1E3A5F',
                cursor: 'pointer',
                background: selected === det.id ? '#0D1B2A' : 'transparent',
                borderLeft: `3px solid ${selected === det.id ? CONFIDENCE_COLOR[det.confidence] : 'transparent'}`,
                transition: 'all 0.15s',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <span style={{
                  fontSize: 11, fontWeight: 'bold', padding: '2px 6px',
                  borderRadius: 3,
                  background: CONFIDENCE_COLOR[det.confidence] + '22',
                  color: CONFIDENCE_COLOR[det.confidence],
                }}>
                  {det.confidence.toUpperCase()}
                </span>
                <span style={{ fontSize: 11, color: '#78909C' }}>
                  {new Date(det.detected_at).toLocaleString()}
                </span>
              </div>
              <div style={{ fontSize: 12, color: '#B0BEC5' }}>
                {det.latitude.toFixed(5)}, {det.longitude.toFixed(5)}
              </div>
              <div style={{ fontSize: 11, color: '#546E7A', marginTop: 2 }}>
                {det.source} · {det.images.length} imagen{det.images.length !== 1 ? 'es' : ''}
                {det.temperature && ` · ${det.temperature}°C`}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Panel derecho: imágenes ── */}
      <div style={{ overflowY: 'auto', padding: 24 }}>
        {!selectedDet ? (
          <div style={{
            height: '100%', display: 'flex',
            alignItems: 'center', justifyContent: 'center',
            color: '#1E3A5F', fontSize: 14,
          }}>
            Seleccioná una detección para ver sus imágenes
          </div>
        ) : (
          <>
            {/* Info */}
            <div style={{ marginBottom: 24 }}>
              <div style={{ fontSize: 16, fontWeight: 'bold', marginBottom: 8 }}>
                Detección — {new Date(selectedDet.detected_at).toLocaleString()}
              </div>
              <div style={{ display: 'flex', gap: 16, fontSize: 12, color: '#78909C' }}>
                <span>Confianza: <span style={{ color: CONFIDENCE_COLOR[selectedDet.confidence] }}>
                  {selectedDet.confidence}
                </span></span>
                <span>Fuente: {selectedDet.source}</span>
                {selectedDet.altitude && <span>Altitud: {selectedDet.altitude}m</span>}
                {selectedDet.raw_confidence_score && (
                  <span>Score: {(selectedDet.raw_confidence_score * 100).toFixed(0)}%</span>
                )}
              </div>
            </div>

            {/* Imágenes */}
            {selectedDet.images.length === 0 ? (
              <div style={{ color: '#546E7A' }}>Sin imágenes guardadas.</div>
            ) : (
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
                gap: 16,
              }}>
                {selectedDet.images.map(img => (
                  <div key={img.id} style={{
                    background: '#0D1B2A',
                    border: '1px solid #1E3A5F',
                    borderRadius: 8,
                    overflow: 'hidden',
                  }}>
                    <img
                      src={`http://localhost:8000${img.url}`}
                      alt={img.image_type}
                      style={{ width: '100%', display: 'block' }}
                    />
                    <div style={{ padding: '8px 12px', fontSize: 11, color: '#78909C' }}>
                      {img.image_type.replace('_', ' ').toUpperCase()}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

function btnStyle(bg: string): React.CSSProperties {
  return {
    background: bg, color: '#78909C', border: 'none',
    borderRadius: 4, padding: '6px 10px', fontSize: 11,
    cursor: 'pointer', fontFamily: 'monospace',
  }
}