import { useState } from 'react'
import { Dashboard } from './pages/Dashboard'
import { MissionsHistory } from './pages/MissionsHistory'

type View = 'dashboard' | 'history'

function App() {
  const [view, setView] = useState<View>('dashboard')

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: '#0A0E1A' }}>

      {/* ── Barra de navegación ── */}
      <nav style={{
        display: 'flex', alignItems: 'center', gap: 4,
        padding: '0 16px', height: 44, flexShrink: 0,
        borderBottom: '1px solid #1E2D3D',
        background: '#0D1B2A',
      }}>
        <span style={{ fontFamily: 'monospace', fontWeight: 'bold', color: '#FF6D00', fontSize: 14, marginRight: 16 }}>
          AeroSearch AI
        </span>

        {(['dashboard', 'history'] as View[]).map(v => {
          const labels: Record<View, string> = { dashboard: 'Dashboard', history: 'Historial' }
          const active = view === v
          return (
            <button
              key={v}
              onClick={() => setView(v)}
              style={{
                background: 'none',
                border: 'none',
                borderBottom: active ? '2px solid #FF6D00' : '2px solid transparent',
                color: active ? '#FF6D00' : '#546E7A',
                fontFamily: 'monospace',
                fontSize: 13,
                padding: '0 12px',
                height: '100%',
                cursor: 'pointer',
                transition: 'color .2s',
              }}
            >
              {labels[v]}
            </button>
          )
        })}
      </nav>

      {/* ── Contenido ── */}
      <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
        {/* Dashboard siempre montado para mantener los WebSockets activos */}
        <div style={{ flex: 1, minHeight: 0, display: view === 'dashboard' ? 'flex' : 'none', flexDirection: 'column' }}>
          <Dashboard />
        </div>
        {view === 'history' && <MissionsHistory />}
      </div>

    </div>
  )
}

export default App
