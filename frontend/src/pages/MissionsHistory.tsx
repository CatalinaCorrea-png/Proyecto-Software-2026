import { useState, useEffect } from 'react'
import { useMissions, type MissionDetail, type Mission } from '../hooks/useMissions'

// ── Helpers ─────────────────────────────────────────────────────────────────

function formatDate(iso: string | null): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('es-AR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function formatDuration(start: string | null, end: string | null): string {
  if (!start) return '—'
  if (!end) return 'En curso'
  const secs = Math.floor((new Date(end).getTime() - new Date(start).getTime()) / 1000)
  const m = Math.floor(secs / 60)
  const s = secs % 60
  return `${m}m ${s}s`
}

function formatCoord(lat: number, lng: number): string {
  const latDir = lat >= 0 ? 'N' : 'S'
  const lngDir = lng >= 0 ? 'E' : 'O'
  return `${Math.abs(lat).toFixed(4)}° ${latDir}, ${Math.abs(lng).toFixed(4)}° ${lngDir}`
}

function areaHa(rows: number, cols: number): string {
  return ((rows * cols * 20 * 20) / 10_000).toFixed(1)
}

function batteryUsed(initial: number, final: number | null): string {
  if (final === null) return '—'
  return `${(initial - final).toFixed(1)}%`
}

const SOURCE_LABEL: Record<string, string> = {
  fusion: 'RGB + Térmica',
  rgb: 'Solo RGB',
  thermal: 'Solo Térmica',
}

// ── Reverse geocoding (Nominatim / OpenStreetMap) ────────────────────────────

const zoneCache = new Map<string, string>()

async function fetchZoneName(lat: number, lng: number): Promise<string> {
  const key = `${lat.toFixed(3)},${lng.toFixed(3)}`
  if (zoneCache.has(key)) return zoneCache.get(key)!
  try {
    const res = await fetch(
      `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&format=json&zoom=10&accept-language=es`,
      { headers: { 'User-Agent': 'AeroSearch-AI/1.0' } }
    )
    const data = await res.json()
    const addr = data.address ?? {}
    const parts = [
      addr.peak ?? addr.leisure ?? addr.natural ?? addr.suburb ?? addr.village ?? addr.town ?? addr.city,
      addr.county ?? addr.municipality,
      addr.state,
    ].filter(Boolean).slice(0, 3) as string[]
    const name = parts.length
      ? parts.join(', ')
      : (data.display_name as string).split(',').slice(0, 2).join(',').trim()
    zoneCache.set(key, name)
    return name
  } catch {
    return formatCoord(lat, lng)
  }
}

// ── Subcomponents ────────────────────────────────────────────────────────────

function StatBox({ label, value, accent }: { label: string; value: string; accent?: string }) {
  return (
    <div style={{
      background: '#0D1B2A',
      borderRadius: 6,
      padding: '8px 12px',
      display: 'flex',
      flexDirection: 'column',
      gap: 2,
    }}>
      <span style={{ fontSize: 10, color: '#546E7A', textTransform: 'uppercase', letterSpacing: 1 }}>
        {label}
      </span>
      <span style={{ fontSize: 15, fontWeight: 'bold', color: accent ?? '#E0E0E0', fontFamily: 'monospace' }}>
        {value}
      </span>
    </div>
  )
}

function CoverageBar({ value }: { value: number | null }) {
  const pct = value ?? 0
  const color = pct >= 75 ? '#00C853' : pct >= 40 ? '#FF6D00' : '#78909C'
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <span style={{ fontSize: 10, color: '#546E7A', textTransform: 'uppercase', letterSpacing: 1 }}>Cobertura</span>
        <span style={{ fontSize: 12, color, fontFamily: 'monospace', fontWeight: 'bold' }}>{pct.toFixed(1)}%</span>
      </div>
      <div style={{ background: '#0D1B2A', borderRadius: 4, height: 6, overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 4, transition: 'width .4s' }} />
      </div>
    </div>
  )
}

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string; border: string }> = {
  active:    { label: '● En curso',   color: '#00C853', bg: 'rgba(0,200,83,.15)',   border: '#00C853' },
  completed: { label: '✓ Completada', color: '#78909C', bg: 'rgba(120,144,156,.15)', border: '#37474F' },
  aborted:   { label: '✕ Interrumpida', color: '#FF3D00', bg: 'rgba(255,61,0,.12)', border: '#FF3D00' },
}

function StatusBadge({ status }: { status: string }) {
  const cfg = STATUS_CONFIG[status] ?? STATUS_CONFIG.completed
  return (
    <span style={{
      fontSize: 10, fontWeight: 'bold', letterSpacing: 1, whiteSpace: 'nowrap',
      textTransform: 'uppercase', padding: '2px 8px', borderRadius: 10,
      background: cfg.bg, color: cfg.color, border: `1px solid ${cfg.border}`,
    }}>
      {cfg.label}
    </span>
  )
}

function MissionCard({ mission, onSelect }: { mission: Mission; onSelect: () => void }) {
  const [zoneName, setZoneName] = useState<string>('…')

  useEffect(() => {
    fetchZoneName(mission.grid_center_lat, mission.grid_center_lng).then(setZoneName)
  }, [mission.grid_center_lat, mission.grid_center_lng])

  return (
    <div
      onClick={onSelect}
      style={{
        background: '#111B2B',
        border: '1px solid #1E2D3D',
        borderRadius: 10,
        padding: 16,
        cursor: 'pointer',
        transition: 'border-color .2s, transform .1s',
        display: 'flex',
        flexDirection: 'column',
        gap: 12,
      }}
      onMouseEnter={e => {
        (e.currentTarget as HTMLDivElement).style.borderColor = '#FF6D00'
        ;(e.currentTarget as HTMLDivElement).style.transform = 'translateY(-2px)'
      }}
      onMouseLeave={e => {
        (e.currentTarget as HTMLDivElement).style.borderColor = '#1E2D3D'
        ;(e.currentTarget as HTMLDivElement).style.transform = 'translateY(0)'
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ fontFamily: 'monospace', fontWeight: 'bold', color: '#FF6D00', fontSize: 16 }}>
            Misión #{mission.id}
          </div>
          <div style={{ fontSize: 13, color: '#E0E0E0', marginTop: 3, maxWidth: 260 }}>
            {zoneName}
          </div>
        </div>
        <StatusBadge status={mission.status} />
      </div>

      {/* Zona geográfica */}
      <div style={{ background: '#0D1B2A', borderRadius: 6, padding: '8px 12px' }}>
        <div style={{ fontFamily: 'monospace', fontSize: 12, color: '#00BCD4' }}>
          {formatCoord(mission.grid_center_lat, mission.grid_center_lng)}
        </div>
        <div style={{ fontSize: 11, color: '#546E7A', marginTop: 2 }}>
          Área: {areaHa(mission.grid_rows, mission.grid_cols)} ha
          &nbsp;·&nbsp;
          Grilla {mission.grid_rows}×{mission.grid_cols}
        </div>
      </div>

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8 }}>
        <StatBox label="Inicio" value={formatDate(mission.started_at)} />
        <StatBox label="Duración" value={formatDuration(mission.started_at, mission.ended_at)} />
        <StatBox label="Batería usada" value={batteryUsed(mission.initial_battery, mission.final_battery)} accent="#FF6D00" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
        <StatBox
          label="Detecciones"
          value={String(mission.detections_count)}
          accent={mission.detections_count > 0 ? '#FF3D00' : '#78909C'}
        />
        <StatBox
          label="Batería final"
          value={mission.final_battery !== null ? `${mission.final_battery.toFixed(1)}%` : '—'}
        />
      </div>

      <CoverageBar value={mission.coverage_percent} />

      <div style={{ fontSize: 11, color: '#546E7A', textAlign: 'right' }}>
        Ver detalle →
      </div>
    </div>
  )
}

function DetectionRow({ det }: { det: MissionDetail['detections'][number] }) {
  const isHigh = det.confidence === 'high'
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '80px 1fr 1fr 80px 80px',
      gap: 8,
      padding: '8px 12px',
      borderBottom: '1px solid #1E2D3D',
      fontSize: 12,
      fontFamily: 'monospace',
      alignItems: 'center',
    }}>
      <span style={{
        padding: '2px 6px', borderRadius: 8, textAlign: 'center', fontSize: 10, fontWeight: 'bold',
        background: isHigh ? 'rgba(255,61,0,.15)' : 'rgba(255,109,0,.15)',
        color: isHigh ? '#FF3D00' : '#FF6D00',
        border: `1px solid ${isHigh ? '#FF3D00' : '#FF6D00'}`,
      }}>
        {isHigh ? 'ALTA' : 'MEDIA'}
      </span>
      <span style={{ color: '#78909C' }}>
        {formatCoord(det.position_lat, det.position_lng)}
      </span>
      <span style={{ color: '#B0BEC5' }}>
        {SOURCE_LABEL[det.source] ?? det.source}
      </span>
      <span style={{ color: det.temperature ? '#FF6D00' : '#37474F' }}>
        {det.temperature ? `${det.temperature.toFixed(1)}°C` : '—'}
      </span>
      <span style={{ color: '#546E7A', fontSize: 10 }}>
        {new Date(det.timestamp).toLocaleTimeString('es-AR')}
      </span>
    </div>
  )
}

function MissionDetailPanel({ missionId, onClose, fetchDetail }: {
  missionId: number
  onClose: () => void
  fetchDetail: (id: number) => Promise<MissionDetail | null>
}) {
  const [detail, setDetail] = useState<MissionDetail | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDetail(missionId).then(d => { setDetail(d); setLoading(false) })
  }, [missionId])

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,.7)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 1000, padding: 20,
    }}
      onClick={onClose}
    >
      <div
        style={{
          background: '#111B2B', border: '1px solid #1E2D3D', borderRadius: 12,
          width: '100%', maxWidth: 820, maxHeight: '85vh',
          display: 'flex', flexDirection: 'column', overflow: 'hidden',
        }}
        onClick={e => e.stopPropagation()}
      >
        {/* Header modal */}
        <div style={{
          padding: '16px 20px', borderBottom: '1px solid #1E2D3D',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        }}>
          <div>
            <span style={{ fontFamily: 'monospace', fontWeight: 'bold', color: '#FF6D00', fontSize: 18 }}>
              Misión #{missionId}
            </span>
            {detail && (
              <span style={{ marginLeft: 12, fontSize: 12, color: '#546E7A' }}>
                {formatDate(detail.started_at)} · {formatDuration(detail.started_at, detail.ended_at)}
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none', border: '1px solid #37474F', color: '#78909C',
              borderRadius: 6, padding: '4px 12px', cursor: 'pointer', fontSize: 13,
            }}
          >
            Cerrar
          </button>
        </div>

        {loading && (
          <div style={{ padding: 40, textAlign: 'center', color: '#546E7A', fontFamily: 'monospace' }}>
            Cargando...
          </div>
        )}

        {detail && (
          <div style={{ overflowY: 'auto', flex: 1 }}>
            {/* Stats del detalle */}
            <div style={{ padding: '16px 20px', display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, borderBottom: '1px solid #1E2D3D' }}>
              <StatBox label="Zona" value={formatCoord(detail.grid_center_lat, detail.grid_center_lng)} accent="#00BCD4" />
              <StatBox label="Cobertura" value={`${(detail.coverage_percent ?? 0).toFixed(1)}%`} accent="#00C853" />
              <StatBox label="Detecciones" value={String(detail.detections.length)} accent="#FF3D00" />
              <StatBox label="Batería consumida" value={batteryUsed(detail.initial_battery, detail.final_battery)} accent="#FF6D00" />
            </div>

            {/* Tabla de detecciones */}
            <div style={{ padding: '12px 20px 4px', fontSize: 11, color: '#546E7A', textTransform: 'uppercase', letterSpacing: 1 }}>
              Detecciones ({detail.detections.length})
            </div>

            {detail.detections.length === 0 ? (
              <div style={{ padding: '20px', textAlign: 'center', color: '#37474F', fontFamily: 'monospace' }}>
                Sin detecciones registradas
              </div>
            ) : (
              <>
                <div style={{
                  display: 'grid', gridTemplateColumns: '80px 1fr 1fr 80px 80px',
                  gap: 8, padding: '6px 12px', fontSize: 10,
                  color: '#37474F', textTransform: 'uppercase', letterSpacing: 1,
                }}>
                  <span>Confianza</span><span>Posición GPS</span>
                  <span>Fuente</span><span>Temp.</span><span>Hora</span>
                </div>
                {detail.detections.map(d => <DetectionRow key={d.id} det={d} />)}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

// ── Main page ────────────────────────────────────────────────────────────────

export function MissionsHistory() {
  const { missions, loading, refetch, fetchDetail } = useMissions()
  const [selectedId, setSelectedId] = useState<number | null>(null)

  return (
    <div style={{
      flex: 1, minHeight: 0, overflowY: 'auto',
      background: '#0A0E1A', padding: '24px 32px',
      fontFamily: 'monospace',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: 24 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 22, fontWeight: 'bold', color: '#FF6D00' }}>
            Historial de Misiones
          </h1>
          <p style={{ margin: '4px 0 0', fontSize: 12, color: '#546E7A' }}>
            {missions.length} misión{missions.length !== 1 ? 'es' : ''} registrada{missions.length !== 1 ? 's' : ''}
          </p>
        </div>
        <button
          onClick={refetch}
          style={{
            background: 'none', border: '1px solid #37474F', color: '#78909C',
            borderRadius: 6, padding: '6px 14px', cursor: 'pointer', fontSize: 12,
          }}
        >
          ↻ Actualizar
        </button>
      </div>

      {/* Content */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: 60, color: '#546E7A' }}>
          Cargando misiones...
        </div>
      ) : missions.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 60, color: '#37474F' }}>
          No hay misiones registradas todavía.
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(380px, 1fr))', gap: 16 }}>
          {missions.map(m => (
            <MissionCard key={m.id} mission={m} onSelect={() => setSelectedId(m.id)} />
          ))}
        </div>
      )}

      {selectedId !== null && (
        <MissionDetailPanel missionId={selectedId} onClose={() => setSelectedId(null)} fetchDetail={fetchDetail} />
      )}
    </div>
  )
}
