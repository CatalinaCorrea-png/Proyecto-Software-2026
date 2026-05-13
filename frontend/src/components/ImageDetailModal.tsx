import type { ImageMeta } from '../types'

const C = {
  panel:   '#0D1220',
  border:  'rgba(255,255,255,0.06)',
  orange:  '#FF6D00',
  muted:   '#78909C',
  text:    '#CFD8DC',
  success: '#00E5FF',
}

interface Props {
  image: ImageMeta
  fullUrl: string
  onClose: () => void
}

function Label({ children }: { children: React.ReactNode }) {
  return (
    <span style={{
      fontFamily: 'monospace', fontSize: 10, letterSpacing: 2,
      color: C.muted, textTransform: 'uppercase' as const,
      display: 'block', marginBottom: 2,
    }}>
      {children}
    </span>
  )
}

export function ImageDetailModal({ image, fullUrl, onClose }: Props) {
  return (
    <div
      style={{
        position: 'fixed', inset: 0,
        background: 'rgba(5,8,16,0.94)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        zIndex: 9999,
        backdropFilter: 'blur(4px)',
      }}
      onClick={onClose}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{
          background: C.panel,
          border: `1px solid rgba(255,109,0,0.3)`,
          borderRadius: 8,
          padding: 24,
          maxWidth: 740,
          width: '90vw',
          maxHeight: '90vh',
          overflowY: 'auto',
          boxShadow: '0 0 60px rgba(255,109,0,0.12)',
          position: 'relative' as const,
        }}
      >
        {/* Corner accents */}
        {[
          { top: 0, left: 0, borderTop: `2px solid ${C.orange}`, borderLeft: `2px solid ${C.orange}`, width: 20, height: 20 },
          { top: 0, right: 0, borderTop: `2px solid ${C.orange}`, borderRight: `2px solid ${C.orange}`, width: 20, height: 20 },
          { bottom: 0, left: 0, borderBottom: `2px solid ${C.orange}`, borderLeft: `2px solid ${C.orange}`, width: 20, height: 20 },
          { bottom: 0, right: 0, borderBottom: `2px solid ${C.orange}`, borderRight: `2px solid ${C.orange}`, width: 20, height: 20 },
        ].map((s, i) => (
          <div key={i} style={{ position: 'absolute', ...s }} />
        ))}

        <img
          src={fullUrl}
          alt="imagen completa"
          style={{ width: '100%', borderRadius: 4, display: 'block', border: `1px solid ${C.border}` }}
        />

        <div style={{
          marginTop: 16,
          paddingTop: 16,
          borderTop: `1px solid ${C.border}`,
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '12px 24px',
          fontFamily: 'monospace',
        }}>
          {([
            ['MISIÓN',     image.mission_id],
            ['TIMESTAMP',  new Date(image.timestamp).toLocaleString()],
            ['LATITUD',    image.lat.toFixed(6)],
            ['LONGITUD',   image.lng.toFixed(6)],
            ['ALTITUD',    `${image.altitude_m.toFixed(1)} m`],
            ['MODO',       image.view_mode.toUpperCase()],
          ] as [string, string][]).map(([lbl, val]) => (
            <div key={lbl}>
              <Label>{lbl}</Label>
              <span style={{ color: C.text, fontSize: 13 }}>{val}</span>
            </div>
          ))}
          <div>
            <Label>DETECCIONES</Label>
            <span style={{ color: C.orange, fontWeight: 'bold', fontSize: 18 }}>
              {image.detection_count}
            </span>
          </div>
          <div>
            <Label>ALT. VUELO</Label>
            <span style={{ color: C.success, fontSize: 13 }}>
              {image.altitude_m.toFixed(1)} m
            </span>
          </div>
        </div>

        <button
          onClick={onClose}
          style={{
            marginTop: 20,
            background: 'transparent',
            color: C.muted,
            border: `1px solid ${C.border}`,
            borderRadius: 4,
            padding: '7px 20px',
            cursor: 'pointer',
            fontFamily: 'monospace',
            fontSize: 11,
            letterSpacing: 1,
            transition: 'border-color 0.15s, color 0.15s',
          }}
          onMouseEnter={e => {
            (e.target as HTMLElement).style.borderColor = C.orange
            ;(e.target as HTMLElement).style.color = C.orange
          }}
          onMouseLeave={e => {
            (e.target as HTMLElement).style.borderColor = C.border
            ;(e.target as HTMLElement).style.color = C.muted
          }}
        >
          ✕ CERRAR
        </button>
      </div>
    </div>
  )
}
