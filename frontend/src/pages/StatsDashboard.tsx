import { useEffect, useState, useMemo } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, Legend, ScatterChart, Scatter, ZAxis,
} from 'recharts'

interface OverviewData {
  ttfd_per_mission:       { label: string; ttfd_min: number }[]
  sweep_efficiency:       { label: string; m2_per_min: number }[]
  detection_density:      { label: string; detections_per_km2: number }[]
  battery_per_km2:        { label: string; battery_per_km2: number }[]
  source_per_mission:     { label: string; rgb: number; thermal: number; fusion: number }[]
  altitude_vs_confidence: { position_altitude: number; rgb_confidence: number; source: string }[]
}

const SOURCE_COLORS: Record<string, string> = {
  rgb:     '#29B6F6',
  thermal: '#FF7043',
  fusion:  '#AB47BC',
}

const tooltipStyle = {
  backgroundColor: '#0D1B2A',
  border: '1px solid #1E3A5F',
  borderRadius: 6,
  color: '#E0E0E0',
  fontFamily: 'monospace',
  fontSize: 12,
}

const axisStyle   = { fill: '#78909C', fontFamily: 'monospace', fontSize: 11 }
const gridStyle2  = { stroke: '#1E3A5F' }

function EmptyState({ message }: { message: string }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      height: 200, color: '#546E7A', fontFamily: 'monospace', fontSize: 12,
    }}>
      {message}
    </div>
  )
}

function Card({ title, children, fullWidth }: {
  title: string; children: React.ReactNode; fullWidth?: boolean
}) {
  return (
    <div style={{
      background: '#0D1B2A', border: '1px solid #1E3A5F', borderRadius: 8,
      padding: '16px 20px',
      ...(fullWidth ? { gridColumn: '1 / -1' } : {}),
    }}>
      <div style={{
        fontFamily: 'monospace', fontSize: 11, fontWeight: 'bold',
        color: '#78909C', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 12,
      }}>
        {title}
      </div>
      {children}
    </div>
  )
}

function MissionFilter({
  missions, selected, onChange,
}: {
  missions: string[]
  selected: Set<string>
  onChange: (s: Set<string>) => void
}) {
  return (
    <div style={{
      background: '#0D1B2A', border: '1px solid #1E3A5F', borderRadius: 8,
      padding: '12px 16px', marginBottom: 20,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
        <span style={{
          fontFamily: 'monospace', fontSize: 11, fontWeight: 'bold',
          color: '#78909C', textTransform: 'uppercase', letterSpacing: 1,
        }}>
          Misiones
        </span>
        <button
          onClick={() => onChange(new Set(missions))}
          style={ctrlBtn}
        >
          Todas
        </button>
        <button
          onClick={() => onChange(new Set())}
          style={ctrlBtn}
        >
          Ninguna
        </button>
        <span style={{ fontFamily: 'monospace', fontSize: 11, color: '#37474F', marginLeft: 'auto' }}>
          {selected.size}/{missions.length} seleccionadas
        </span>
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
        {missions.map(m => {
          const active = selected.has(m)
          return (
            <button
              key={m}
              onClick={() => {
                const next = new Set(selected)
                if (next.has(m)) next.delete(m)
                else next.add(m)
                onChange(next)
              }}
              style={{
                padding: '3px 10px', borderRadius: 12, cursor: 'pointer',
                fontFamily: 'monospace', fontSize: 11,
                border: `1px solid ${active ? '#29B6F6' : '#37474F'}`,
                background: active ? 'rgba(41,182,246,0.12)' : 'transparent',
                color: active ? '#29B6F6' : '#546E7A',
              }}
            >
              {m}
            </button>
          )
        })}
      </div>
    </div>
  )
}

const ctrlBtn: React.CSSProperties = {
  padding: '2px 10px', borderRadius: 4, cursor: 'pointer',
  fontFamily: 'monospace', fontSize: 11,
  border: '1px solid #37474F', background: 'transparent', color: '#90A4AE',
}

export function StatsDashboard() {
  const [data, setData]       = useState<OverviewData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState<string | null>(null)
  const [selected, setSelected] = useState<Set<string>>(new Set())

  useEffect(() => {
    fetch('http://localhost:8000/api/stats/overview')
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() })
      .then((d: OverviewData) => {
        setData(d)
        setSelected(new Set([
          ...d.ttfd_per_mission.map(x => x.label),
          ...d.sweep_efficiency.map(x => x.label),
          ...d.detection_density.map(x => x.label),
          ...d.battery_per_km2.map(x => x.label),
          ...d.source_per_mission.map(x => x.label),
        ]))
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const allLabels = useMemo(() => {
    if (!data) return []
    return Array.from(new Set([
      ...data.ttfd_per_mission.map(d => d.label),
      ...data.sweep_efficiency.map(d => d.label),
      ...data.detection_density.map(d => d.label),
      ...data.battery_per_km2.map(d => d.label),
      ...data.source_per_mission.map(d => d.label),
    ]))
  }, [data])

  const f = <T extends { label: string }>(arr: T[]) => arr.filter(d => selected.has(d.label))

  const sourceNorm = useMemo(() =>
    (data?.source_per_mission ?? [])
      .filter(d => selected.has(d.label))
      .map(d => {
        const total = d.rgb + d.thermal + d.fusion || 1
        return {
          label:   d.label,
          rgb:     +((d.rgb     / total) * 100).toFixed(1),
          thermal: +((d.thermal / total) * 100).toFixed(1),
          fusion:  +((d.fusion  / total) * 100).toFixed(1),
        }
      })
  , [data, selected])

  const scatterBySource = useMemo(() =>
    ['rgb', 'thermal', 'fusion'].map(src => ({
      src,
      points: (data?.altitude_vs_confidence ?? []).filter(d => d.source === src),
    })).filter(g => g.points.length > 0)
  , [data])

  if (loading) return (
    <div style={containerStyle}>
      <p style={{ color: '#78909C', fontFamily: 'monospace', fontSize: 13 }}>Cargando estadísticas...</p>
    </div>
  )

  if (error) return (
    <div style={containerStyle}>
      <p style={{ color: '#EF5350', fontFamily: 'monospace', fontSize: 13 }}>Error: {error}</p>
    </div>
  )

  return (
    <div style={containerStyle}>
      <h2 style={titleStyle}>Estadísticas Operacionales</h2>

      {allLabels.length > 0 && (
        <MissionFilter missions={allLabels} selected={selected} onChange={setSelected} />
      )}

      <div style={gridStyle}>

        {/* TTFD */}
        <Card title="Tiempo hasta primera detección (min)">
          {f(data!.ttfd_per_mission).length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={f(data!.ttfd_per_mission)} margin={{ top: 8, right: 16, left: 0, bottom: 48 }}>
                <CartesianGrid strokeDasharray="3 3" {...gridStyle2} vertical={false} />
                <XAxis dataKey="label" tick={axisStyle} angle={-35} textAnchor="end" interval={0} />
                <YAxis tick={axisStyle} unit=" min" />
                <Tooltip contentStyle={tooltipStyle} cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                  formatter={(v) => [`${v} min`, 'TTFD']} />
                <Bar dataKey="ttfd_min" radius={[4, 4, 0, 0]} fill="#FF7043" />
              </BarChart>
            </ResponsiveContainer>
          ) : <EmptyState message="Sin misiones con detecciones registradas" />}
        </Card>

        {/* Eficiencia de barrido */}
        <Card title="Eficiencia de barrido (m²/min)">
          {f(data!.sweep_efficiency).length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={f(data!.sweep_efficiency)} margin={{ top: 8, right: 16, left: 0, bottom: 48 }}>
                <CartesianGrid strokeDasharray="3 3" {...gridStyle2} vertical={false} />
                <XAxis dataKey="label" tick={axisStyle} angle={-35} textAnchor="end" interval={0} />
                <YAxis tick={axisStyle} />
                <Tooltip contentStyle={tooltipStyle} cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                  formatter={(v) => [`${v} m²/min`, 'Eficiencia']} />
                <Bar dataKey="m2_per_min" radius={[4, 4, 0, 0]} fill="#66BB6A" />
              </BarChart>
            </ResponsiveContainer>
          ) : <EmptyState message="Sin misiones completadas aún" />}
        </Card>

        {/* Densidad de detecciones */}
        <Card title="Densidad de detecciones (det/km²)">
          {f(data!.detection_density).length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={f(data!.detection_density)} margin={{ top: 8, right: 16, left: 0, bottom: 48 }}>
                <CartesianGrid strokeDasharray="3 3" {...gridStyle2} vertical={false} />
                <XAxis dataKey="label" tick={axisStyle} angle={-35} textAnchor="end" interval={0} />
                <YAxis tick={axisStyle} />
                <Tooltip contentStyle={tooltipStyle} cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                  formatter={(v) => [`${v} det/km²`, 'Densidad']} />
                <Bar dataKey="detections_per_km2" radius={[4, 4, 0, 0]} fill="#EF5350" />
              </BarChart>
            </ResponsiveContainer>
          ) : <EmptyState message="Sin misiones con cobertura registrada" />}
        </Card>

        {/* Batería por km² */}
        <Card title="Consumo de batería por km² cubierto (%/km²)">
          {f(data!.battery_per_km2).length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={f(data!.battery_per_km2)} margin={{ top: 8, right: 16, left: 0, bottom: 48 }}>
                <CartesianGrid strokeDasharray="3 3" {...gridStyle2} vertical={false} />
                <XAxis dataKey="label" tick={axisStyle} angle={-35} textAnchor="end" interval={0} />
                <YAxis tick={axisStyle} unit="%/km²" />
                <Tooltip contentStyle={tooltipStyle} cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                  formatter={(v) => [`${v}%/km²`, 'Batería/km²']} />
                <Bar dataKey="battery_per_km2" radius={[4, 4, 0, 0]} fill="#FFA726" />
              </BarChart>
            </ResponsiveContainer>
          ) : <EmptyState message="Sin misiones completadas con batería registrada" />}
        </Card>

        {/* Fuente de detección — 100% stacked */}
        <Card title="Fuente de detección por misión — proporción (RGB / Térmica / Fusión)" fullWidth>
          {sourceNorm.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={sourceNorm} margin={{ top: 8, right: 16, left: 0, bottom: 48 }}>
                <CartesianGrid strokeDasharray="3 3" {...gridStyle2} vertical={false} />
                <XAxis dataKey="label" tick={axisStyle} angle={-35} textAnchor="end" interval={0} />
                <YAxis tick={axisStyle} domain={[0, 100]} unit="%" allowDecimals={false} />
                <Tooltip
                  contentStyle={tooltipStyle}
                  cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                  formatter={(v, name) => [`${v}%`, String(name)]}
                />
                <Legend wrapperStyle={{ fontFamily: 'monospace', fontSize: 11, color: '#90A4AE', paddingTop: 16 }} />
                <Bar dataKey="rgb"     name="RGB"     stackId="a" fill={SOURCE_COLORS.rgb}     radius={[0, 0, 0, 0]} />
                <Bar dataKey="thermal" name="Térmica" stackId="a" fill={SOURCE_COLORS.thermal} radius={[0, 0, 0, 0]} />
                <Bar dataKey="fusion"  name="Fusión"  stackId="a" fill={SOURCE_COLORS.fusion}  radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <EmptyState message="Sin detecciones registradas" />}
        </Card>

        {/* Altitud vs confianza — sin filtro por misión (datos a nivel detección) */}
        <Card title="Altitud vs confianza RGB (scatter — todas las misiones)" fullWidth>
          {scatterBySource.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <ScatterChart margin={{ top: 8, right: 24, left: 0, bottom: 8 }}>
                <CartesianGrid strokeDasharray="3 3" {...gridStyle2} />
                <XAxis
                  dataKey="position_altitude" name="Altitud" type="number"
                  tick={axisStyle} unit="m" label={{ value: 'Altitud (m)', position: 'insideBottom', offset: -4, fill: '#546E7A', fontSize: 11 }}
                />
                <YAxis
                  dataKey="rgb_confidence" name="Confianza" type="number" domain={[0, 1]}
                  tick={axisStyle} label={{ value: 'Confianza RGB', angle: -90, position: 'insideLeft', fill: '#546E7A', fontSize: 11 }}
                />
                <ZAxis range={[20, 20]} />
                <Tooltip
                  contentStyle={tooltipStyle}
                  cursor={{ strokeDasharray: '3 3' }}
                  formatter={(v, name) => [
                    name === 'Altitud' ? `${v} m` : Number(v).toFixed(3),
                    name,
                  ]}
                />
                <Legend wrapperStyle={{ fontFamily: 'monospace', fontSize: 11, color: '#90A4AE' }} />
                {scatterBySource.map(({ src, points }) => (
                  <Scatter
                    key={src}
                    name={src === 'rgb' ? 'RGB' : src === 'thermal' ? 'Térmica' : 'Fusión'}
                    data={points}
                    fill={SOURCE_COLORS[src]}
                    opacity={0.7}
                  />
                ))}
              </ScatterChart>
            </ResponsiveContainer>
          ) : <EmptyState message="Sin datos de confianza RGB registrados" />}
        </Card>

      </div>
    </div>
  )
}

const containerStyle: React.CSSProperties = {
  padding: '24px 32px',
  minHeight: '100%',
  background: '#060E18',
  overflowY: 'auto',
}

const titleStyle: React.CSSProperties = {
  fontFamily: 'monospace', fontSize: 16, fontWeight: 'bold',
  color: '#E0E0E0', marginBottom: 24, letterSpacing: 1,
}

const gridStyle: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: '1fr 1fr',
  gap: 20,
}
