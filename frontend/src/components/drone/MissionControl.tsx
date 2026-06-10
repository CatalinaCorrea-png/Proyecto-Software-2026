import { useState } from 'react'
import type { DroneTelemetry } from '../../types'

const API = 'http://localhost:8000'

interface MissionControlProps {
  telemetry: DroneTelemetry | null
}

const STATE_LABEL: Record<string, { text: string; color: string }> = {
  idle:                  { text: 'EN ESPERA',        color: '#78909C' },
  sweeping:              { text: 'BARRIENDO',        color: '#00C853' },
  awaiting_confirmation: { text: 'DETECCIÓN',        color: '#FF5252' },
  revisiting:            { text: 'REVISITANDO',      color: '#00BCD4' },
  revisit_confirm:       { text: 'REVISIÓN',         color: '#00BCD4' },
  returning_home:        { text: 'VOLVIENDO A BASE', color: '#00BCD4' },
  completed:             { text: 'MISIÓN COMPLETA',  color: '#00C853' },
}

export function MissionControl({ telemetry }: MissionControlProps) {
  const [busy, setBusy] = useState(false)
  const [showQueue, setShowQueue] = useState(false)

  const sweepState = telemetry?.sweep_state ?? 'idle'
  const paused = telemetry?.paused ?? false
  const pending = telemetry?.pending_detection ?? null
  const revisit = telemetry?.revisit_queue ?? []

  const isHigh = sweepState === 'awaiting_confirmation' && !!pending
  const isRevisitConfirm = sweepState === 'revisit_confirm' && !!pending
  const awaiting = isHigh || isRevisitConfirm
  const cardColor = isHigh ? '#FF5252' : '#00BCD4'
  const isRevisiting = sweepState === 'revisiting' || sweepState === 'revisit_confirm'
  const canStartRevisit = revisit.length > 0 && !isRevisiting && !awaiting

  const post = async (path: string, body?: unknown) => {
    setBusy(true)
    try {
      await fetch(`${API}${path}`, {
        method: 'POST',
        headers: body ? { 'Content-Type': 'application/json' } : undefined,
        body: body ? JSON.stringify(body) : undefined,
      })
    } catch { /* backend caído */ } finally {
      setBusy(false)
    }
  }

  const badge = paused
    ? { text: 'PAUSADO', color: '#FFC107' }
    : STATE_LABEL[sweepState] ?? STATE_LABEL.idle

  return (
    <div style={{
      background: '#0D1B2A',
      border: `1px solid ${awaiting ? cardColor : '#1E3A5F'}`,
      borderRadius: 6,
      padding: '8px 10px',
      display: 'flex',
      flexDirection: 'column',
      gap: 8,
      transition: 'border-color 0.2s',
    }}>

      {/* Header con badge de estado */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ color: '#78909C', fontSize: 11, fontFamily: 'monospace', letterSpacing: 1 }}>
          MISIÓN AUTÓNOMA
        </span>
        <span style={{
          display: 'inline-flex', alignItems: 'center', gap: 5,
          fontSize: 10, fontFamily: 'monospace', fontWeight: 'bold',
          letterSpacing: 1, color: badge.color,
        }}>
          <span style={{
            width: 7, height: 7, borderRadius: '50%',
            background: badge.color, boxShadow: `0 0 6px ${badge.color}`,
          }} />
          {badge.text}
        </span>
      </div>

      {/* Card de confirmación de detección (alta confianza o punto de revisita) */}
      {awaiting && pending && (
        <div style={{
          border: `1px solid ${cardColor}55`, borderRadius: 5,
          background: `${cardColor}0D`, padding: '8px 10px',
          display: 'flex', flexDirection: 'column', gap: 8,
        }}>
          <div style={{ fontFamily: 'monospace', fontSize: 11, color: cardColor }}>
            {isHigh
              ? 'Detección de alta confianza — dron detenido'
              : 'Punto de revisita — confirmá o descartá'}
          </div>
          <div style={{ fontFamily: 'monospace', fontSize: 10, color: '#90A4AE', lineHeight: 1.5 }}>
            Fuente: {pending.source}
            {pending.temperature != null && <> · {pending.temperature}°C</>}<br />
            {pending.position.lat.toFixed(5)}, {pending.position.lng.toFixed(5)}
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button
              disabled={busy}
              onClick={() => post('/mission/detection/resolve', { action: 'confirm' })}
              style={btn('#00C853')}
            >
              ✓ CONFIRMAR
            </button>
            <button
              disabled={busy}
              onClick={() => post('/mission/detection/resolve', { action: 'dismiss' })}
              style={btn('#FF5252')}
            >
              ✕ DESCARTAR
            </button>
          </div>
        </div>
      )}

      {/* Cola de revisita (detecciones MEDIUM) */}
      {revisit.length > 0 && (
        <div style={{ borderTop: '1px solid #0F1E2E', paddingTop: 8 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <button
              onClick={() => setShowQueue(s => !s)}
              style={{
                background: 'transparent', border: 'none', padding: 0, cursor: 'pointer',
                display: 'inline-flex', alignItems: 'center', gap: 6,
                fontFamily: 'monospace', fontSize: 10, letterSpacing: 1, color: '#FFD600',
              }}
            >
              <span style={{ fontSize: 8 }}>{showQueue ? '▼' : '▶'}</span>
              PARA REVISAR ({revisit.length})
            </button>
            <button
              disabled={busy}
              onClick={() => post('/mission/revisit/clear')}
              style={{
                background: 'transparent', border: 'none', cursor: 'pointer',
                fontFamily: 'monospace', fontSize: 9, letterSpacing: 1, color: '#546E7A',
              }}
            >
              LIMPIAR
            </button>
          </div>

          {showQueue && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginTop: 6, maxHeight: 120, overflowY: 'auto' }}>
              {revisit.map(d => (
                <div key={d.id} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  fontFamily: 'monospace', fontSize: 9, color: '#90A4AE',
                  background: '#FFD6000D', border: '1px solid #FFD60022',
                  borderRadius: 4, padding: '3px 6px',
                }}>
                  <span>
                    {d.source}
                    {d.temperature != null && <> · {d.temperature}°C</>}
                    {' · '}{d.position.lat.toFixed(4)}, {d.position.lng.toFixed(4)}
                  </span>
                  <button
                    disabled={busy}
                    onClick={() => post('/mission/revisit/dismiss', { id: d.id })}
                    title="Descartar (falso positivo)"
                    style={{
                      background: 'transparent', border: 'none', cursor: 'pointer',
                      color: '#FF5252', fontSize: 11, fontWeight: 'bold', padding: '0 2px',
                    }}
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          )}

          {canStartRevisit && (
            <button
              disabled={busy}
              onClick={() => post('/mission/revisit/start')}
              style={{ ...btn('#00BCD4'), width: '100%', marginTop: 8 }}
            >
              ↩ REVISAR AHORA ({revisit.length})
            </button>
          )}
        </div>
      )}

      {/* Pausa / Reanudar (deshabilitado mientras hay confirmación pendiente) */}
      <button
        disabled={busy || !!awaiting}
        onClick={() => post(paused ? '/mission/resume' : '/mission/pause')}
        style={{
          ...btn(paused ? '#00C853' : '#FFC107'),
          opacity: awaiting ? 0.4 : 1,
          cursor: awaiting ? 'not-allowed' : 'pointer',
        }}
      >
        {paused ? '▶ REANUDAR' : '⏸ PAUSAR'}
      </button>

    </div>
  )
}

function btn(color: string): React.CSSProperties {
  return {
    flex: 1,
    padding: '6px 0',
    fontSize: 10,
    fontFamily: 'monospace',
    fontWeight: 'bold',
    letterSpacing: 1,
    border: `1px solid ${color}`,
    borderRadius: 4,
    background: `${color}1A`,
    color,
    cursor: 'pointer',
    transition: 'all 0.2s',
  }
}
