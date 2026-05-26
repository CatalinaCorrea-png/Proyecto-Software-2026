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
const axisStyle = { fill: '#78909C', fontFamily: 'monospace', fontSize: 11 }
const gridColor = { stroke: '#1E3A5F' }

const ROW_H    = 34
const MIN_H    = 80
const barH     = (n: number) => Math.max(MIN_H, n * ROW_H) + 24
const MARGIN_H = { top: 4, right: 52, left: 0, bottom: 4 }
const Y_WIDTH  = 100

function EmptyState({ message }: { message: string }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      height: 120, color: '#546E7A', fontFamily: 'monospace', fontSize: 12,
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

const sectionLabel: React.CSSProperties = {
  fontFamily: 'monospace', fontSize: 10, fontWeight: 'bold',
  color: '#546E7A', textTransform: 'uppercase', letterSpacing: 1,
  marginBottom: 8,
}
const miniBtn: React.CSSProperties = {
  padding: '2px 8px', borderRadius: 3, cursor: 'pointer',
  fontFamily: 'monospace', fontSize: 10,
  border: '1px solid #37474F', background: 'transparent', color: '#78909C',
}

function Sidebar({ allLabels, excluded, onExcludedChange }: {
  allLabels: string[]
  excluded: Set<string>
  onExcludedChange: (s: Set<string>) => void
}) {
  const activeCount = allLabels.filter(l => !excluded.has(l)).length

  return (
    <aside style={{
      width: 188, flexShrink: 0,
      background: '#080F19', borderRight: '1px solid #1E3A5F',
      padding: '24px 16px', display: 'flex', flexDirection: 'column',
    }}>
      <div style={{
        fontFamily: 'monospace', fontSize: 11, fontWeight: 'bold',
        color: '#78909C', letterSpacing: 1, marginBottom: 16,
      }}>
        FILTROS
      </div>

      <div style={sectionLabel}>Misiones</div>
      <div style={{ display: 'flex', gap: 6, marginBottom: 10 }}>
        <button onClick={() => onExcludedChange(new Set())} style={miniBtn}>Todas</button>
        <button onClick={() => onExcludedChange(new Set(allLabels))} style={miniBtn}>Ninguna</button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 6, overflowY: 'auto', flex: 1 }}>
        {allLabels.map(m => {
          const checked = !excluded.has(m)
          return (
            <label key={m} style={{ display: 'flex', alignItems: 'flex-start', gap: 8, cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={checked}
                onChange={() => {
                  const next = new Set(excluded)
                  if (next.has(m)) next.delete(m)
                  else next.add(m)
                  onExcludedChange(next)
                }}
                style={{ marginTop: 2, accentColor: '#29B6F6', cursor: 'pointer', flexShrink: 0 }}
              />
              <span style={{
                fontFamily: 'monospace', fontSize: 11,
                color: checked ? '#90A4AE' : '#37474F',
                wordBreak: 'break-word', lineHeight: 1.4,
              }}>
                {m}
              </span>
            </label>
          )
        })}
      </div>

      <div style={{ borderTop: '1px solid #1E3A5F', marginTop: 16, paddingTop: 12 }}>
        <div style={{ fontFamily: 'monospace', fontSize: 10, color: '#37474F' }}>
          {activeCount} de {allLabels.length} activas
        </div>
      </div>
    </aside>
  )
}

export function StatsDashboard() {
  const [data, setData]         = useState<OverviewData | null>(null)
  const [loading, setLoading]   = useState(true)
  const [error, setError]       = useState<string | null>(null)
  const [excluded, setExcluded] = useState<Set<string>>(new Set())

  useEffect(() => {
    fetch('http://localhost:8000/api/stats/overview')
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() })
      .then(setData)
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

  const f = <T extends { label: string }>(arr: T[]) =>
    arr.filter(d => !excluded.has(d.label))

  const sourceNorm = useMemo(() =>
    f(data?.source_per_mission ?? []).map(d => {
      const total = d.rgb + d.thermal + d.fusion || 1
      return {
        label:   d.label,
        rgb:     +((d.rgb     / total) * 100).toFixed(1),
        thermal: +((d.thermal / total) * 100).toFixed(1),
        fusion:  +((d.fusion  / total) * 100).toFixed(1),
      }
    })
  , [data, excluded])  // eslint-disable-line react-hooks/exhaustive-deps

  const scatterBySource = useMemo(() =>
    ['rgb', 'thermal', 'fusion'].map(src => ({
      src,
      points: (data?.altitude_vs_confidence ?? []).filter(d => d.source === src),
    })).filter(g => g.points.length > 0)
  , [data])

  if (loading) return (
    <div style={pageStyle}>
      <p style={{ color: '#78909C', fontFamily: 'monospace', fontSize: 13, padding: 32 }}>Cargando estadísticas...</p>
    </div>
  )
  if (error) return (
    <div style={pageStyle}>
      <p style={{ color: '#EF5350', fontFamily: 'monospace', fontSize: 13, padding: 32 }}>Error: {error}</p>
    </div>
  )

  const ttfd      = f(data!.ttfd_per_mission)
  const sweep     = f(data!.sweep_efficiency)
  const density   = f(data!.detection_density)
  const battery   = f(data!.battery_per_km2)

  return (
    <div style={pageStyle}>
      {allLabels.length > 0 && (
        <Sidebar allLabels={allLabels} excluded={excluded} onExcludedChange={setExcluded} />
      )}

      <div style={{ flex: 1, padding: '24px 28px', overflowY: 'auto' }}>
        <h2 style={titleStyle}>Estadísticas Operacionales</h2>

        <div style={gridStyle}>

          {/* TTFD */}
          <Card title="Tiempo hasta primera detección (min)">
            {ttfd.length > 0 ? (
              <ResponsiveContainer width="100%" height={barH(ttfd.length)}>
                <BarChart layout="vertical" data={ttfd} margin={MARGIN_H}>
                  <CartesianGrid strokeDasharray="3 3" {...gridColor} horizontal={false} />
                  <XAxis type="number" tick={axisStyle} unit=" min" />
                  <YAxis type="category" dataKey="label" tick={axisStyle} width={Y_WIDTH} interval={0} />
                  <Tooltip contentStyle={tooltipStyle} cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                    formatter={(v) => [`${v} min`, 'TTFD']} />
                  <Bar dataKey="ttfd_min" radius={[0, 4, 4, 0]} fill="#FF7043"
                    label={{ position: 'right', fontSize: 10, fill: '#78909C', fontFamily: 'monospace' }} />
                </BarChart>
              </ResponsiveContainer>
            ) : <EmptyState message="Sin misiones con detecciones registradas" />}
          </Card>

          {/* Eficiencia de barrido */}
          <Card title="Eficiencia de barrido (m²/min)">
            {sweep.length > 0 ? (
              <ResponsiveContainer width="100%" height={barH(sweep.length)}>
                <BarChart layout="vertical" data={sweep} margin={MARGIN_H}>
                  <CartesianGrid strokeDasharray="3 3" {...gridColor} horizontal={false} />
                  <XAxis type="number" tick={axisStyle} />
                  <YAxis type="category" dataKey="label" tick={axisStyle} width={Y_WIDTH} interval={0} />
                  <Tooltip contentStyle={tooltipStyle} cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                    formatter={(v) => [`${v} m²/min`, 'Eficiencia']} />
                  <Bar dataKey="m2_per_min" radius={[0, 4, 4, 0]} fill="#66BB6A"
                    label={{ position: 'right', fontSize: 10, fill: '#78909C', fontFamily: 'monospace' }} />
                </BarChart>
              </ResponsiveContainer>
            ) : <EmptyState message="Sin misiones completadas aún" />}
          </Card>

          {/* Densidad de detecciones */}
          <Card title="Densidad de detecciones (det/km²)">
            {density.length > 0 ? (
              <ResponsiveContainer width="100%" height={barH(density.length)}>
                <BarChart layout="vertical" data={density} margin={MARGIN_H}>
                  <CartesianGrid strokeDasharray="3 3" {...gridColor} horizontal={false} />
                  <XAxis type="number" tick={axisStyle} />
                  <YAxis type="category" dataKey="label" tick={axisStyle} width={Y_WIDTH} interval={0} />
                  <Tooltip contentStyle={tooltipStyle} cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                    formatter={(v) => [`${v} det/km²`, 'Densidad']} />
                  <Bar dataKey="detections_per_km2" radius={[0, 4, 4, 0]} fill="#EF5350"
                    label={{ position: 'right', fontSize: 10, fill: '#78909C', fontFamily: 'monospace' }} />
                </BarChart>
              </ResponsiveContainer>
            ) : <EmptyState message="Sin misiones con cobertura registrada" />}
          </Card>

          {/* Batería por km² */}
          <Card title="Consumo de batería por km² cubierto (%/km²)">
            {battery.length > 0 ? (
              <ResponsiveContainer width="100%" height={barH(battery.length)}>
                <BarChart layout="vertical" data={battery} margin={MARGIN_H}>
                  <CartesianGrid strokeDasharray="3 3" {...gridColor} horizontal={false} />
                  <XAxis type="number" tick={axisStyle} unit="%/km²" />
                  <YAxis type="category" dataKey="label" tick={axisStyle} width={Y_WIDTH} interval={0} />
                  <Tooltip contentStyle={tooltipStyle} cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                    formatter={(v) => [`${v}%/km²`, 'Batería/km²']} />
                  <Bar dataKey="battery_per_km2" radius={[0, 4, 4, 0]} fill="#FFA726"
                    label={{ position: 'right', fontSize: 10, fill: '#78909C', fontFamily: 'monospace' }} />
                </BarChart>
              </ResponsiveContainer>
            ) : <EmptyState message="Sin misiones completadas con batería registrada" />}
          </Card>

          {/* Fuente de detección — 100% stacked horizontal */}
          <Card title="Fuente de detección por misión — proporción (RGB / Térmica / Fusión)" fullWidth>
            {sourceNorm.length > 0 ? (
              <ResponsiveContainer width="100%" height={barH(sourceNorm.length)}>
                <BarChart layout="vertical" data={sourceNorm} margin={MARGIN_H}>
                  <CartesianGrid strokeDasharray="3 3" {...gridColor} horizontal={false} />
                  <XAxis type="number" tick={axisStyle} domain={[0, 100]} unit="%" allowDecimals={false} />
                  <YAxis type="category" dataKey="label" tick={axisStyle} width={Y_WIDTH} interval={0} />
                  <Tooltip
                    contentStyle={tooltipStyle}
                    cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                    formatter={(v, name) => [`${v}%`, String(name)]}
                  />
                  <Legend wrapperStyle={{ fontFamily: 'monospace', fontSize: 11, color: '#90A4AE', paddingTop: 12 }} />
                  <Bar dataKey="rgb"     name="RGB"     stackId="a" fill={SOURCE_COLORS.rgb}     radius={[0, 0, 0, 0]} />
                  <Bar dataKey="thermal" name="Térmica" stackId="a" fill={SOURCE_COLORS.thermal} radius={[0, 0, 0, 0]} />
                  <Bar dataKey="fusion"  name="Fusión"  stackId="a" fill={SOURCE_COLORS.fusion}  radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : <EmptyState message="Sin detecciones registradas" />}
          </Card>

          {/* Altitud vs confianza */}
          <Card title="Altitud vs confianza RGB (scatter — todas las misiones)" fullWidth>
            {scatterBySource.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <ScatterChart margin={{ top: 8, right: 24, left: 0, bottom: 24 }}>
                  <CartesianGrid strokeDasharray="3 3" {...gridColor} />
                  <XAxis
                    dataKey="position_altitude" name="Altitud" type="number"
                    tick={axisStyle} unit="m"
                    label={{ value: 'Altitud (m)', position: 'insideBottom', offset: -12, fill: '#546E7A', fontSize: 11 }}
                  />
                  <YAxis
                    dataKey="rgb_confidence" name="Confianza" type="number" domain={[0, 1]}
                    tick={axisStyle}
                    label={{ value: 'Confianza RGB', angle: -90, position: 'insideLeft', fill: '#546E7A', fontSize: 11 }}
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
    </div>
  )
}

const pageStyle: React.CSSProperties = {
  display: 'flex',
  minHeight: '100%',
  background: '#060E18',
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
