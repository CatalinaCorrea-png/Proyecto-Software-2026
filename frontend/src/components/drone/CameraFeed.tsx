import { useEffect, useRef, useState } from 'react'
import type { Detection } from '../../types'
import type { Metrics } from './PerformancePanel'

export interface FusedDetection {
  confidence: 'high' | 'medium' | 'low'
  source: string
  temperature?: number
}

export interface FramePayload {
  type: 'frame'
  frame: string
  thermal_overlay?: string
  thermal_frame: string
  fused_detections: FusedDetection[]
  detection_count: number
  metrics: Metrics
}

interface Props {
  framePayload: FramePayload | null
  isConnected: boolean
  expanded?: boolean
}

type ViewMode = 'rgb' | 'overlay' | 'thermal'

const VIEW_LABELS: Record<ViewMode, string> = {
  rgb: 'RGB', overlay: 'OVERLAY', thermal: 'TÉRMICA'
}

export function CameraFeed({ framePayload, isConnected, expanded = false }: Props) {
  const [viewMode, setViewMode] = useState<ViewMode>('rgb')

  const currentFrame =
    viewMode === 'rgb' ? framePayload?.frame
    : viewMode === 'overlay' ? (framePayload?.thermal_overlay ?? framePayload?.frame)
    : framePayload?.thermal_frame

  return (
    <div style={{
      background: '#0D1B2A',
      border: expanded ? 'none' : '1px solid #1E3A5F',
      borderRadius: expanded ? 0 : 8,
      padding: expanded ? 16 : 12,
      display: 'flex',
      flexDirection: 'column',
      gap: 8,
      height: expanded ? '100%' : 'auto',
      minHeight: 0,
      boxSizing: 'border-box',
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
        {(['rgb', 'overlay', 'thermal'] as ViewMode[]).map(mode => (
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
            {VIEW_LABELS[mode]}
          </button>
        ))}
      </div>

      {/* Frame — ocupa el espacio disponible */}
      <div style={{ flex: 1, borderRadius: 4, overflow: 'hidden', minHeight: 0 }}>
        {currentFrame ? (
          <img
            src={`data:image/jpeg;base64,${currentFrame}`}
            style={{
              width: '100%', height: 'auto',
              objectFit: 'cover', display: 'block',
              imageRendering: viewMode === 'thermal' ? 'pixelated' : 'auto'
            }}
            alt="camera feed"
          />
        ) : (
          <div style={{
            background: '#060D14', height: expanded ? '100%' : 140, minHeight: 120,
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