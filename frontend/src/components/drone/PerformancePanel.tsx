interface ProcessingMetrics {
  yolo_ms: number,
  thermal_ms: number,
  fusion_ms: number,
  encode_ms: number,
  total_ms: number,
}

interface DetectionMetrics {
  total: number,
  high: number,
  frames: number,
  rate: number,
}

export interface Metrics {
  fps: number,
  processing: ProcessingMetrics,
  detections: DetectionMetrics
}

interface Props {
  metrics: Metrics | null
}

export function PerformancePanel({ metrics }: Props) {
  const totalMs = metrics?.processing.total_ms ?? 0
  const fps = metrics?.fps ?? 0

  // Color según rendimiento
  const fpsColor = fps >= 12 ? '#00C853' : fps >= 7 ? '#FFD600' : '#FF5252'
  const latColor = totalMs < 100 ? '#00C853' : totalMs < 200 ? '#FFD600' : '#FF5252'

  return (
    <div style={{
      background: '#0D1B2A',
      border: '1px solid #1A2E45',
      borderRadius: 10,
      padding: '12px 14px',
      display: 'flex',
      flexDirection: 'column',
      gap: 10,
    }}>
      {/* Header */}
      <div style={{
        fontSize: 9, color: '#455A64',
        letterSpacing: 2, fontFamily: 'monospace'
      }}>
        RENDIMIENTO
      </div>

      {/* FPS + Latencia — los más importantes, grandes */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
        <MetricBig
          label="FPS"
          value={fps.toFixed(1)}
          color={fpsColor}
          sub="cámara"
        />
        <MetricBig
          label="LATENCIA"
          value={`${totalMs.toFixed(0)}ms`}
          color={latColor}
          sub="total frame"
        />
      </div>

      {/* Desglose del pipeline */}
      <div style={{
        borderTop: '1px solid #1A2E45',
        paddingTop: 8,
        display: 'flex',
        flexDirection: 'column',
        gap: 5,
      }}>
        <div style={{ fontSize: 9, color: '#455A64', letterSpacing: 2, marginBottom: 2 }}>
          PIPELINE
        </div>
        <PipelineBar label="YOLO"    ms={metrics?.processing.yolo_ms}    total={totalMs} color="#FF6D00" />
        <PipelineBar label="TÉRMICA" ms={metrics?.processing.thermal_ms} total={totalMs} color="#00BCD4" />
        <PipelineBar label="FUSIÓN"  ms={metrics?.processing.fusion_ms}  total={totalMs} color="#A78BFA" />
        <PipelineBar label="ENCODE"  ms={metrics?.processing.encode_ms}  total={totalMs} color="#78909C" />
      </div>

      {/* Detecciones */}
      <div style={{
        borderTop: '1px solid #1A2E45',
        paddingTop: 8,
        display: 'grid',
        gridTemplateColumns: '1fr 1fr 1fr',
        gap: 6,
      }}>
        <MetricSmall label="FRAMES"  value={String(metrics?.detections.frames ?? 0)} />
        <MetricSmall label="DET"     value={String(metrics?.detections.total ?? 0)} color="#FFD600" />
        <MetricSmall label="HIGH"    value={String(metrics?.detections.high ?? 0)}  color="#00C853" />
      </div>
    </div>
  )
}

// ── Sub-componentes ───────────────────────────────────────────────────────────

function MetricBig({ label, value, color = '#E0E8F0', sub }: {
  label: string; value: string; color?: string; sub?: string
}) {
  return (
    <div style={{
      background: '#070E18',
      borderRadius: 8,
      padding: '8px 10px',
      border: '1px solid #1A2E45',
    }}>
      <div style={{ fontSize: 9, color: '#455A64', letterSpacing: 2, marginBottom: 4 }}>
        {label}
      </div>
      <div style={{ fontSize: 22, fontWeight: 'bold', color, lineHeight: 1 }}>
        {value}
      </div>
      {sub && (
        <div style={{ fontSize: 9, color: '#455A64', marginTop: 3 }}>
          {sub}
        </div>
      )}
    </div>
  )
}

function MetricSmall({ label, value, color = '#78909C' }: {
  label: string; value: string; color?: string
}) {
  return (
    <div style={{ textAlign: 'center' }}>
      <div style={{ fontSize: 9, color: '#455A64', letterSpacing: 1 }}>{label}</div>
      <div style={{ fontSize: 14, fontWeight: 'bold', color, marginTop: 2 }}>{value}</div>
    </div>
  )
}

function PipelineBar({ label, ms, total, color }: {
  label: string; ms?: number; total: number; color: string
}) {
  const value = ms ?? 0
  const pct = total > 0 ? Math.min((value / total) * 100, 100) : 0

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      {/* Label */}
      <div style={{
        width: 50, fontSize: 9,
        color: '#455A64', letterSpacing: 1,
        flexShrink: 0
      }}>
        {label}
      </div>

      {/* Barra */}
      <div style={{
        flex: 1, height: 4,
        background: '#1A2E45',
        borderRadius: 2,
        overflow: 'hidden',
      }}>
        <div style={{
          width: `${pct}%`,
          height: '100%',
          background: color,
          borderRadius: 2,
          transition: 'width 0.3s ease',
          boxShadow: `0 0 4px ${color}`,
        }} />
      </div>

      {/* Valor */}
      <div style={{
        width: 40, fontSize: 9,
        color, textAlign: 'right',
        flexShrink: 0
      }}>
        {value.toFixed(0)}ms
      </div>
    </div>
  )
}