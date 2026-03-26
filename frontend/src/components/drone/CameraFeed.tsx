import { useEffect, useRef, useState } from 'react'
import { useDetectionFeed } from '../../hooks/useDetectionFeed'
import type { Detection } from '../../types'

// Actualizar el tipo en useDetectionFeed.ts también:
// thermal_overlay: string  ← agregar este campo a FramePayload

interface Props {
  onNewDetection?: (detection: Detection) => void
}

type ViewMode = 'rgb' | 'overlay' | 'thermal'

export function CameraFeed({ onNewDetection }: Props) {
  const { framePayload, detections, isConnected } = useDetectionFeed('ws://localhost:8000/ws/detection')
  const [viewMode, setViewMode] = useState<ViewMode>('rgb')
  const lastDetectionRef = useRef<string | null>(null)

  useEffect(() => {
    if (detections.length === 0) return
    const latest = detections[0]
    if (latest.id !== lastDetectionRef.current) {
      lastDetectionRef.current = latest.id
      onNewDetection?.(latest)
    }
  }, [detections, onNewDetection])

  const confidenceColor = (c: string) =>
    c === 'high' ? '#00C853' : c === 'medium' ? '#FFD600' : '#FF5252'

  const currentFrame = viewMode === 'rgb'
    ? framePayload?.frame
    : viewMode === 'overlay'
    ? framePayload?.thermal_overlay
    : framePayload?.thermal_frame

  const viewLabels: Record<ViewMode, string> = {
    rgb: 'RGB',
    overlay: 'OVERLAY',
    thermal: 'TÉRMICA'
  }

  return (
    <div style={{
      background: '#0D1B2A',
      border: '1px solid #1E3A5F',
      borderRadius: '8px',
      padding: '12px',
      display: 'flex',
      flexDirection: 'column',
      gap: 8
    }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ color: '#78909C', fontSize: 11, fontFamily: 'monospace' }}>
          CÁMARA EN VIVO
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          {framePayload && framePayload.detection_count > 0 && (
            <span style={{
              background: '#FF6D00', color: 'white',
              fontSize: 10, padding: '2px 6px', borderRadius: 4,
              fontFamily: 'monospace', fontWeight: 'bold'
            }}>
              {framePayload.detection_count} DETECCIÓN{framePayload.detection_count > 1 ? 'ES' : ''}
            </span>
          )}
          <div style={{
            width: 8, height: 8, borderRadius: '50%',
            background: isConnected ? '#00C853' : '#FF5252'
          }} />
        </div>
      </div>

      {/* Toggle de vista */}
      <div style={{ display: 'flex', gap: 4 }}>
        {(['rgb', 'overlay', 'thermal'] as ViewMode[]).map(mode => (
          <button
            key={mode}
            onClick={() => setViewMode(mode)}
            style={{
              flex: 1,
              padding: '4px 0',
              fontSize: 10,
              fontFamily: 'monospace',
              fontWeight: 'bold',
              border: 'none',
              borderRadius: 4,
              cursor: 'pointer',
              background: viewMode === mode ? '#00BCD4' : '#1E3A5F',
              color: viewMode === mode ? '#0A0E1A' : '#78909C',
              transition: 'all 0.15s'
            }}
          >
            {viewLabels[mode]}
          </button>
        ))}
      </div>

      {/* Frame */}
      <div style={{ position: 'relative', borderRadius: 4, overflow: 'hidden' }}>
        {currentFrame ? (
          <img
            src={`data:image/jpeg;base64,${currentFrame}`}
            style={{
              width: '100%', display: 'block',
              imageRendering: viewMode === 'thermal' ? 'pixelated' : 'auto'
            }}
            alt="camera feed"
          />
        ) : (
          <div style={{
            background: '#060D14', height: 140,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#1E3A5F', fontSize: 12, fontFamily: 'monospace'
          }}>
            SIN SEÑAL
          </div>
        )}
      </div>

      {/* Detecciones del frame */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        {framePayload?.fused_detections.map((det, i) => (
          <div key={i} style={{
            display: 'flex', alignItems: 'center', gap: 6,
            fontFamily: 'monospace', fontSize: 11
          }}>
            <div style={{
              width: 6, height: 6, borderRadius: '50%',
              background: confidenceColor(det.confidence), flexShrink: 0
            }} />
            <span style={{ color: confidenceColor(det.confidence) }}>
              {det.confidence}
            </span>
            <span style={{ color: '#78909C' }}>
              {det.source}
              {'temperature' in det && det.temperature
                ? ` · ${(det.temperature as number).toFixed(1)}°C`
                : ''}
            </span>
          </div>
        ))}
        {(!framePayload || framePayload.fused_detections.length === 0) && (
          <span style={{ color: '#1E3A5F', fontSize: 11, fontFamily: 'monospace' }}>
            sin detecciones
          </span>
        )}
      </div>

      {detections.length > 0 && (
        <div style={{
          borderTop: '1px solid #1E3A5F', paddingTop: 8,
          color: '#78909C', fontSize: 10, fontFamily: 'monospace'
        }}>
          📍 {detections.length} evento{detections.length > 1 ? 's' : ''} en el mapa
        </div>
      )}
    </div>
  )
}