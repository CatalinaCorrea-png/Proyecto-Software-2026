const C = {
  panel:  '#0D1220',
  border: 'rgba(255,255,255,0.06)',
  danger: '#FF5252',
  muted:  '#78909C',
  text:   '#CFD8DC',
}

interface Props {
  onClose: () => void
}

// Ícono de "desconectado": un conector hembra y uno macho separados por un
// hueco con un destello, como un cable/enchufe desenchufado — en el mismo
// rojo que usa el resto de la app para acciones/estados destructivos.
function UnpluggedIcon() {
  return (
    <svg width="200" height="100" viewBox="0 0 100 60" fill="none" stroke={C.danger} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      {/* cordón izquierdo + conector hembra */}
      <path d="M15 20 C 6 20, 10 6, 2 3" />
      <path d="M38 12 H26 A12 12 0 0 0 26 36 H38 Z" />

      {/* conector macho con sus clavijas apuntando al hueco */}
      <path d="M62 12 H74 A12 12 0 0 1 74 36 H62 Z" />
      <line x1="62" y1="19" x2="50" y2="19" />
      <line x1="62" y1="29" x2="50" y2="29" />
      {/* cordón derecho */}
      <path d="M86 25 C 88 28, 86 49, 97 52" />

      {/* destello de desconexión */}
      <g strokeWidth="1.3" opacity="0.8">
        <line x1="44" y1="10" x2="44" y2="4" />
        <line x1="44" y1="38" x2="44" y2="44" />
        <line x1="34" y1="14" x2="30" y2="9" />
        <line x1="54" y1="14" x2="58" y2="9" />
        <line x1="34" y1="34" x2="30" y2="39" />
        <line x1="54" y1="34" x2="58" y2="39" />
      </g>
    </svg>
  )
}

export function MissionFinishedModal({ onClose }: Props) {
  return (
    <div
      style={{
        position: 'fixed', inset: 0,
        background: 'rgba(5,8,16,0.94)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        zIndex: 9999,
        backdropFilter: 'blur(4px)',
      }}
    >
      <div
        style={{
          background: C.panel,
          border: `1px solid rgba(255,82,82,0.35)`,
          borderRadius: 8,
          padding: '32px 36px',
          width: 380,
          maxWidth: '90vw',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 16,
          textAlign: 'center' as const,
          boxShadow: '0 0 60px rgba(255,82,82,0.15)',
          position: 'relative' as const,
        }}
      >
        {/* Corner accents, mismo patrón visual que ImageDetailModal */}
        {[
          { top: 0, left: 0, borderTop: `2px solid ${C.danger}`, borderLeft: `2px solid ${C.danger}`, width: 20, height: 20 },
          { top: 0, right: 0, borderTop: `2px solid ${C.danger}`, borderRight: `2px solid ${C.danger}`, width: 20, height: 20 },
          { bottom: 0, left: 0, borderBottom: `2px solid ${C.danger}`, borderLeft: `2px solid ${C.danger}`, width: 20, height: 20 },
          { bottom: 0, right: 0, borderBottom: `2px solid ${C.danger}`, borderRight: `2px solid ${C.danger}`, width: 20, height: 20 },
        ].map((s, i) => (
          <div key={i} style={{ position: 'absolute', ...s }} />
        ))}

        <UnpluggedIcon />

        <div style={{ fontFamily: 'monospace', fontSize: 16, fontWeight: 'bold', color: C.danger, letterSpacing: 0.5 }}>
          Misión finalizada
        </div>

        <div style={{ fontFamily: 'monospace', fontSize: 12.5, color: C.text, lineHeight: 1.6 }}>
          La misión ha sido finalizada por el administrador. Ya no se recibirán nuevas actualizaciones.
        </div>

        <button
          onClick={onClose}
          style={{
            marginTop: 8,
            background: 'transparent',
            color: C.muted,
            border: `1px solid ${C.border}`,
            borderRadius: 4,
            padding: '7px 24px',
            cursor: 'pointer',
            fontFamily: 'monospace',
            fontSize: 11,
            letterSpacing: 1,
            transition: 'border-color 0.15s, color 0.15s',
          }}
          onMouseEnter={e => {
            (e.target as HTMLElement).style.borderColor = C.danger
            ;(e.target as HTMLElement).style.color = C.danger
          }}
          onMouseLeave={e => {
            (e.target as HTMLElement).style.borderColor = C.border
            ;(e.target as HTMLElement).style.color = C.muted
          }}
        >
          ENTENDIDO
        </button>
      </div>
    </div>
  )
}
