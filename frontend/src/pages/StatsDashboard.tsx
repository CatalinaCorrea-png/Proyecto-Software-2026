import { useEffect, useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
  PieChart, Pie, Legend, AreaChart, Area, CartesianGrid,
} from 'recharts'

interface OverviewData {
  detections_per_mission: { id: number; label: string; count: number }[]
  confidence_distribution: { name: string; value: number }[]
  source_distribution: { name: string; value: number }[]
  coverage_per_mission: { id: number; label: string; coverage_percent: number }[]
  detections_timeline: { date: string; count: number }[]
}

const CONF_COLORS: Record<string, string> = {
  high: '#EF5350',
  medium: '#FFA726',
  low: '#42A5F5',
}

const SOURCE_COLORS: Record<string, string> = {
  rgb: '#29B6F6',
  thermal: '#FF7043',
  fusion: '#AB47BC',
}

const BAR_COLOR = '#29B6F6'
const COVERAGE_COLOR = '#66BB6A'
const AREA_COLOR = '#29B6F6'

const tooltipStyle = {
  backgroundColor: '#0D1B2A',
  border: '1px solid #1E3A5F',
  borderRadius: 6,
  color: '#E0E0E0',
  fontFamily: 'monospace',
  fontSize: 12,
}

const axisStyle = { fill: '#78909C', fontFamily: 'monospace', fontSize: 11 }

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

export function StatsDashboard() {
  const [data, setData] = useState<OverviewData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch('http://localhost:8000/api/stats/overview')
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div style={containerStyle}>
        <div style={{ color: '#78909C', fontFamily: 'monospace', fontSize: 13 }}>
          Cargando estadísticas...
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div style={containerStyle}>
        <div style={{ color: '#EF5350', fontFamily: 'monospace', fontSize: 13 }}>
          Error al cargar estadísticas: {error}
        </div>
      </div>
    )
  }

  const hasDetections = (data?.detections_per_mission.length ?? 0) > 0
  const hasConfidence = (data?.confidence_distribution.length ?? 0) > 0
  const hasSource = (data?.source_distribution.length ?? 0) > 0
  const hasCoverage = (data?.coverage_per_mission.length ?? 0) > 0
  const hasTimeline = (data?.detections_timeline.length ?? 0) > 0

  return (
    <div style={containerStyle}>
      <h2 style={titleStyle}>Estadísticas de Misiones</h2>

      <div style={gridStyle}>

        {/* Detections per mission */}
        <div style={cardStyle}>
          <div style={cardTitleStyle}>Detecciones por misión</div>
          {hasDetections ? (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart
                data={data!.detections_per_mission}
                margin={{ top: 8, right: 16, left: 0, bottom: 48 }}
              >
                <XAxis dataKey="label" tick={axisStyle} angle={-35} textAnchor="end" interval={0} />
                <YAxis tick={axisStyle} allowDecimals={false} />
                <Tooltip
                  contentStyle={tooltipStyle}
                  cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                  formatter={(v) => [v, 'Detecciones']}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {data!.detections_per_mission.map((_, i) => (
                    <Cell key={i} fill={BAR_COLOR} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState message="Sin datos de detecciones aún" />
          )}
        </div>

        {/* Confidence distribution */}
        <div style={cardStyle}>
          <div style={cardTitleStyle}>Distribución de confianza</div>
          {hasConfidence ? (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={data!.confidence_distribution}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="45%"
                  innerRadius={50}
                  outerRadius={90}
                  label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}
                  labelLine={false}
                >
                  {data!.confidence_distribution.map((entry, i) => (
                    <Cell key={i} fill={CONF_COLORS[entry.name] ?? '#90A4AE'} />
                  ))}
                </Pie>
                <Tooltip contentStyle={tooltipStyle} formatter={(v, name) => [v, name]} />
                <Legend wrapperStyle={{ fontFamily: 'monospace', fontSize: 11, color: '#90A4AE' }} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState message="Sin detecciones registradas aún" />
          )}
        </div>

        {/* Source distribution */}
        <div style={cardStyle}>
          <div style={cardTitleStyle}>Fuente de detección</div>
          {hasSource ? (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={data!.source_distribution}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="45%"
                  innerRadius={50}
                  outerRadius={90}
                  label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}
                  labelLine={false}
                >
                  {data!.source_distribution.map((entry, i) => (
                    <Cell key={i} fill={SOURCE_COLORS[entry.name] ?? '#90A4AE'} />
                  ))}
                </Pie>
                <Tooltip contentStyle={tooltipStyle} formatter={(v, name) => [v, name]} />
                <Legend wrapperStyle={{ fontFamily: 'monospace', fontSize: 11, color: '#90A4AE' }} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState message="Sin detecciones registradas aún" />
          )}
        </div>

        {/* Coverage per mission */}
        <div style={cardStyle}>
          <div style={cardTitleStyle}>Cobertura de grilla por misión (%)</div>
          {hasCoverage ? (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart
                data={data!.coverage_per_mission}
                margin={{ top: 8, right: 16, left: 0, bottom: 48 }}
              >
                <XAxis dataKey="label" tick={axisStyle} angle={-35} textAnchor="end" interval={0} />
                <YAxis tick={axisStyle} domain={[0, 100]} unit="%" />
                <Tooltip
                  contentStyle={tooltipStyle}
                  cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                  formatter={(v) => [`${v}%`, 'Cobertura']}
                />
                <Bar dataKey="coverage_percent" radius={[4, 4, 0, 0]}>
                  {data!.coverage_per_mission.map((_, i) => (
                    <Cell key={i} fill={COVERAGE_COLOR} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState message="Sin misiones completadas con datos de cobertura" />
          )}
        </div>

        {/* Detections over time */}
        <div style={{ ...cardStyle, gridColumn: '1 / -1' }}>
          <div style={cardTitleStyle}>Detecciones en el tiempo</div>
          {hasTimeline ? (
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart
                data={data!.detections_timeline}
                margin={{ top: 8, right: 16, left: 0, bottom: 8 }}
              >
                <defs>
                  <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={AREA_COLOR} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={AREA_COLOR} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E3A5F" vertical={false} />
                <XAxis dataKey="date" tick={axisStyle} />
                <YAxis tick={axisStyle} allowDecimals={false} />
                <Tooltip
                  contentStyle={tooltipStyle}
                  cursor={{ stroke: '#1E3A5F' }}
                  formatter={(v) => [v, 'Detecciones']}
                />
                <Area
                  type="monotone"
                  dataKey="count"
                  stroke={AREA_COLOR}
                  strokeWidth={2}
                  fill="url(#areaGrad)"
                  dot={{ fill: AREA_COLOR, r: 3 }}
                  activeDot={{ r: 5 }}
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState message="Sin detecciones registradas aún" />
          )}
        </div>

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
  fontFamily: 'monospace',
  fontSize: 16,
  fontWeight: 'bold',
  color: '#E0E0E0',
  marginBottom: 24,
  letterSpacing: 1,
}

const gridStyle: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: '1fr 1fr',
  gap: 20,
}

const cardStyle: React.CSSProperties = {
  background: '#0D1B2A',
  border: '1px solid #1E3A5F',
  borderRadius: 8,
  padding: '16px 20px',
}

const cardTitleStyle: React.CSSProperties = {
  fontFamily: 'monospace',
  fontSize: 12,
  fontWeight: 'bold',
  color: '#78909C',
  textTransform: 'uppercase',
  letterSpacing: 1,
  marginBottom: 12,
}
