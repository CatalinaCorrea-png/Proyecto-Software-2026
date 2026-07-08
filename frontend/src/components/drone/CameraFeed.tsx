import { useEffect, useRef, useState } from 'react'
import { useDetectionFeed } from '../../hooks/useDetectionFeed'
import type { Detection } from '../../types'
import { WS_URL } from '../../config'

interface Props {
  onNewDetection?: (detection: Detection) => void
}

type ViewMode = 'rgb' | 'overlay'

export function CameraFeed({ onNewDetection }: Props) {
  const { framePayload, detections, isConnected } = useDetectionFeed(`${WS_URL}/ws/detection`)
  const [viewMode, setViewMode] = useState<ViewMode>('rgb')
  const forwardedRef = useRef<Set<string>>(new Set())

  useEffect(() => {
    for (const det of detections) {
      if (!forwardedRef.current.has(det.id)) {
        forwardedRef.current.add(det.id)
        onNewDetection?.(det)
      }
    }
  }, [detections, onNewDetection])

  const viewLabels: Record<ViewMode, string> = {
    rgb: 'RGB', overlay: 'OVERLAY TÉRMICO'
  }

  return (
    <div style={{
      background: '#0D1B2A',
      border: '1px solid #1E3A5F',
      borderRadius: '6px',
      padding: '8px',
      display: 'flex',
      flexDirection: 'column',
      gap: 6,
      minHeight: 0,
    }}>

      {/* Header — altura fija para que el badge de detecciones no agrande/achique la fila */}
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        height: 22, flexShrink: 0, marginBottom: 8,
      }}>
        <span style={{ color: '#78909C', fontSize: 12, fontFamily: 'monospace' }}>
          CÁMARA EN VIVO
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          {framePayload && framePayload.detection_count > 0 && (
            <span style={{
              background: '#FF6D00', color: 'white',
              fontSize: 8, padding: '2px 6px', borderRadius: 4,
              fontFamily: 'monospace', fontWeight: 'bold'
            }}>
              {framePayload.detection_count} DET
            </span>
          )}
          <div style={{
            width: 8, height: 8, borderRadius: '50%',
            background: isConnected ? '#00C853' : '#FF5252'
          }} />
        </div>
      </div>

      {/* Toggle */}
      <div style={{ display: 'flex', gap: 4 }}>
        {(['rgb', 'overlay'] as ViewMode[]).map(mode => (
          <button
            key={mode}
            onClick={() => setViewMode(mode)}
            style={{
              flex: 1, padding: '4px 0',
              fontSize: 10, fontFamily: 'monospace', fontWeight: 'bold',
              border: 'none', borderRadius: 4, cursor: 'pointer',
              background: viewMode === mode ? '#00BCD4' : '#1E3A5F',
              color: viewMode === mode ? '#0A0E1A' : '#78909C',
              transition: 'all 0.15s'
            }}
          >
            {viewLabels[mode]}
          </button>
        ))}
      </div>

      {/* Frame — ocupa el espacio disponible */}
      <div style={{ flex: 1, borderRadius: 4, overflow: 'hidden', minHeight: 0 }}>
        {framePayload?.frame ? (
          <img
            src={`data:image/jpeg;base64,${
              viewMode === 'rgb' ? framePayload.frame
              : (framePayload.thermal_overlay ?? framePayload.frame)
            }`}
            style={{
              width: '100%', height: 'auto',
              display: 'block',
            }}
            alt="camera feed"
          />
        ) : (
          <div style={{
            background: '#060D14', height: 120, minHeight: 120,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#1E3A5F', fontSize: 12, fontFamily: 'monospace'
          }}>
            SIN SEÑAL
          </div>
        )}
      </div>

    </div>
  )
}