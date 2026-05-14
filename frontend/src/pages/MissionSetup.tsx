import { useState } from 'react'

const API = 'http://localhost:8000'

interface MissionConfig {
  name: string
  lat: number
  lng: number
  altitude: number
  grid_rows: number
  grid_cols: number
  cell_size_m: number
}

const PRESETS: Record<string, Pick<MissionConfig, 'lat' | 'lng'>> = {
  'Aconcagua':    { lat: -32.6532, lng: -70.0109 },
  'Plaza de Mayo': { lat: -34.6083, lng: -58.3712 },
  'UNSAM':        { lat: -34.5735, lng: -58.5270 },
}

interface Props {
  onStart: () => void
}

export function MissionSetup({ onStart }: Props) {
  const [config, setConfig] = useState<MissionConfig>({
    name: '',
    lat: -32.6532,
    lng: -70.0109,
    altitude: 25,
    grid_rows: 20,
    grid_cols: 20,
    cell_size_m: 20,
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const set = <K extends keyof MissionConfig>(key: K, val: MissionConfig[K]) =>
    setConfig(prev => ({ ...prev, [key]: val }))

  const areaW = (config.grid_cols * config.cell_size_m).toFixed(0)
  const areaH = (config.grid_rows * config.cell_size_m).toFixed(0)
  const totalCells = config.grid_rows * config.grid_cols

  const handleSubmit = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await fetch(`${API}/mission/setup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      })
      if (!res.ok) throw new Error(`Error ${res.status}`)
      onStart()
    } catch (e: any) {
      setError(e.message || 'Error de conexión')
    } finally {
      setLoading(false)
    }
  }

  const inputStyle = {
    background: '#0A1628',
    border: '1px solid #1E3A5F',
    borderRadius: 4,
    color: '#E0E0E0',
    fontFamily: 'monospace',
    fontSize: 13,
    padding: '6px 10px',
    width: '100%',
    outline: 'none',
  } as const

  const labelStyle = {
    color: '#78909C',
    fontSize: 10,
    fontFamily: 'monospace',
    letterSpacing: 1,
    marginBottom: 2,
  } as const

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100%',
      background: '#0A0E1A',
      padding: 20,
    }}>
      <div style={{
        background: '#0D1B2A',
        border: '1px solid #1E3A5F',
        borderRadius: 8,
        padding: '28px 32px',
        width: 420,
        display: 'flex',
        flexDirection: 'column',
        gap: 16,
      }}>

        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: 4 }}>
          <div style={{ fontSize: 20, fontWeight: 'bold', color: '#FF6D00', fontFamily: 'monospace' }}>
            AeroSearch AI
          </div>
          <div style={{ fontSize: 11, color: '#546E7A', fontFamily: 'monospace' }}>
            Configurar nueva misión
          </div>
        </div>

        {/* Nombre */}
        <div>
          <div style={labelStyle}>NOMBRE DE MISIÓN</div>
          <input
            style={inputStyle}
            placeholder="Ej: Búsqueda Zona Norte"
            value={config.name}
            onChange={e => set('name', e.target.value)}
          />
        </div>

        {/* Coordenadas */}
        <div>
          <div style={{ ...labelStyle, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>COORDENADAS DE INICIO</span>
            <div style={{ display: 'flex', gap: 4 }}>
              {Object.entries(PRESETS).map(([name, coords]) => (
                <button
                  key={name}
                  onClick={() => { set('lat', coords.lat); set('lng', coords.lng) }}
                  style={{
                    background: config.lat === coords.lat && config.lng === coords.lng
                      ? '#FF6D0020' : 'transparent',
                    border: `1px solid ${config.lat === coords.lat && config.lng === coords.lng
                      ? '#FF6D00' : '#37474F'}`,
                    borderRadius: 3,
                    color: config.lat === coords.lat && config.lng === coords.lng
                      ? '#FF6D00' : '#546E7A',
                    fontSize: 9,
                    fontFamily: 'monospace',
                    padding: '2px 6px',
                    cursor: 'pointer',
                  }}
                >
                  {name}
                </button>
              ))}
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginTop: 4 }}>
            <div>
              <div style={{ ...labelStyle, fontSize: 9 }}>LATITUD</div>
              <input
                type="number"
                step="0.0001"
                style={inputStyle}
                value={config.lat}
                onChange={e => set('lat', parseFloat(e.target.value) || 0)}
              />
            </div>
            <div>
              <div style={{ ...labelStyle, fontSize: 9 }}>LONGITUD</div>
              <input
                type="number"
                step="0.0001"
                style={inputStyle}
                value={config.lng}
                onChange={e => set('lng', parseFloat(e.target.value) || 0)}
              />
            </div>
          </div>
        </div>

        {/* Altitud */}
        <div>
          <div style={labelStyle}>ALTITUD DE VUELO (m)</div>
          <input
            type="number"
            style={inputStyle}
            value={config.altitude}
            onChange={e => set('altitude', parseFloat(e.target.value) || 0)}
          />
        </div>

        {/* Grilla */}
        <div>
          <div style={labelStyle}>GRILLA DE BÚSQUEDA</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8, marginTop: 4 }}>
            <div>
              <div style={{ ...labelStyle, fontSize: 9 }}>FILAS</div>
              <input
                type="number"
                min={2}
                max={50}
                style={inputStyle}
                value={config.grid_rows}
                onChange={e => set('grid_rows', parseInt(e.target.value) || 2)}
              />
            </div>
            <div>
              <div style={{ ...labelStyle, fontSize: 9 }}>COLUMNAS</div>
              <input
                type="number"
                min={2}
                max={50}
                style={inputStyle}
                value={config.grid_cols}
                onChange={e => set('grid_cols', parseInt(e.target.value) || 2)}
              />
            </div>
            <div>
              <div style={{ ...labelStyle, fontSize: 9 }}>CELDA (m)</div>
              <input
                type="number"
                min={5}
                max={100}
                style={inputStyle}
                value={config.cell_size_m}
                onChange={e => set('cell_size_m', parseFloat(e.target.value) || 5)}
              />
            </div>
          </div>
          <div style={{
            marginTop: 6,
            fontSize: 10,
            fontFamily: 'monospace',
            color: '#546E7A',
          }}>
            Área: {areaW}m x {areaH}m — {totalCells} celdas
          </div>
        </div>

        {/* Error */}
        {error && (
          <div style={{ color: '#FF5252', fontSize: 11, fontFamily: 'monospace', textAlign: 'center' }}>
            {error}
          </div>
        )}

        {/* Submit */}
        <button
          onClick={handleSubmit}
          disabled={loading}
          style={{
            background: loading ? '#37474F' : '#FF6D00',
            color: '#fff',
            border: 'none',
            borderRadius: 6,
            padding: '10px 0',
            fontSize: 13,
            fontFamily: 'monospace',
            fontWeight: 'bold',
            letterSpacing: 1,
            cursor: loading ? 'wait' : 'pointer',
            transition: 'background 0.2s',
          }}
        >
          {loading ? 'CONFIGURANDO...' : 'INICIAR MISIÓN'}
        </button>
      </div>
    </div>
  )
}
