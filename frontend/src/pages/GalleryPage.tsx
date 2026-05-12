import { useEffect, useRef, useState } from 'react'
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import L from 'leaflet'
import { useImageGallery } from '../hooks/useImageGallery'
import type { ImageMeta } from '../types'
import 'leaflet/dist/leaflet.css'

const C = {
  bg:          '#0A0E1A',
  panel:       '#0D1220',
  panelHover:  '#111827',
  border:      'rgba(255,255,255,0.06)',
  borderHover: '#FF6D00',
  orange:      '#FF6D00',
  orangeDim:   'rgba(255,109,0,0.15)',
  muted:       '#78909C',
  text:        '#CFD8DC',
  textDim:     '#455A64',
  success:     '#00E5FF',
  grid:        'rgba(255,255,255,0.03)',
}

function dotIcon() {
  return L.divIcon({
    className: '',
    html: `<div style="
      width:12px;height:12px;border-radius:50%;
      background:#FF6D00;border:2px solid #fff;
      box-shadow:0 0 8px rgba(255,109,0,0.8);
    "></div>`,
    iconSize: [12, 12],
    iconAnchor: [6, 6],
  })
}

// ── Scanline overlay ──────────────────────────────────────────────────────────
const scanlineStyle: React.CSSProperties = {
  position: 'fixed',
  inset: 0,
  backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.04) 2px, rgba(0,0,0,0.04) 4px)',
  pointerEvents: 'none',
  zIndex: 0,
}

// ── Section label ─────────────────────────────────────────────────────────────
function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <span style={{
      fontFamily: 'monospace',
      fontSize: 14,
      letterSpacing: 2,
      color: C.muted,
      textTransform: 'uppercase' as const,
      display: 'block',
      marginBottom: 4
    }}>
      {children}
    </span>
  )
}

// ── Card ──────────────────────────────────────────────────────────────────────
function ImageCard({ image, onSelect }: { image: ImageMeta; onSelect: (img: ImageMeta) => void }) {
  const [hovered, setHovered] = useState(false)

  return (
    <div
      onClick={() => onSelect(image)}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        cursor: 'pointer',
        border: `1px solid ${hovered ? C.borderHover : C.border}`,
        borderRadius: 6,
        overflow: 'hidden',
        background: C.panel,
        transition: 'border-color 0.15s, box-shadow 0.15s, transform 0.15s',
        boxShadow: hovered
          ? '0 0 20px rgba(255,109,0,0.18), inset 0 0 0 1px rgba(255,109,0,0.08)'
          : '0 2px 8px rgba(0,0,0,0.4)',
        transform: hovered ? 'translateY(-2px)' : 'none',
        position: 'relative' as const
      }}
    >
      {/* Thumbnail */}
      <div style={{ position: 'relative' }}>
        <img
          src={`data:image/jpeg;base64,${image.thumbnail_b64}`}
          alt="captura"
          style={{ width: '100%', display: 'block', filter: hovered ? 'brightness(1.05)' : 'brightness(0.9)' }}
        />
        {/* Gradient overlay */}
        <div style={{
          position: 'absolute', inset: 0,
          background: 'linear-gradient(to bottom, transparent 50%, rgba(10,14,26,0.7) 100%)',
          pointerEvents: 'none',
        }} />
        {/* Detection badge */}
        <span style={{
          position: 'absolute', top: 8, right: 8,
          background: image.detection_count > 0 ? C.orange : C.textDim,
          color: '#fff',
          borderRadius: 3,
          padding: '2px 7px',
          fontSize: 9,
          fontWeight: 700,
          fontFamily: 'monospace',
          letterSpacing: 1,
        }}>
          {image.detection_count} DET
        </span>
        {/* Corner accent */}
        <div style={{
          position: 'absolute', top: 0, left: 0,
          width: 20, height: 2,
          background: hovered ? C.orange : 'transparent',
          transition: 'background 0.15s',
        }} />
        <div style={{
          position: 'absolute', top: 0, left: 0,
          width: 2, height: 20,
          background: hovered ? C.orange : 'transparent',
          transition: 'background 0.15s',
        }} />
      </div>

      {/* Meta */}
      <div style={{ padding: '10px 12px', fontFamily: 'monospace' }}>
        <div style={{ fontSize: 12, color: C.text, marginBottom: 5 }}>
          {new Date(image.timestamp).toLocaleString()}
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: 10, color: C.muted }}>
            {image.lat.toFixed(5)}, {image.lng.toFixed(5)}
          </span>
        </div>
        <div style={{
          marginTop: 8,
          paddingTop: 8,
          borderTop: `1px solid ${C.border}`,
          display: 'flex',
          gap: 12,
        }}>
          <div >
            <span style={{display: 'flex', fontSize: 14, padding: 0, color: C.muted}}>ALT</span>
            <span style={{ fontSize: 12, color: C.success }}>{image.altitude_m.toFixed(1)} m</span>
          </div>
          <div>
            <span style={{display: 'flex', fontSize: 14, padding: 0, color: C.muted, paddingLeft: 4}}>MODO</span>
            <span style={{ fontSize: 12, color: C.text, paddingLeft: 4 }}>{image.view_mode.toUpperCase()}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Modal ─────────────────────────────────────────────────────────────────────
function ImageModal({ image, fullUrl, onClose }: { image: ImageMeta; fullUrl: string; onClose: () => void }) {
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
          paddingBottom: 16,
          borderTop: `1px solid ${C.border}`,
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '8px 24px',
          fontFamily: 'monospace',
          fontSize: 18,
        }}>
          {[
            ['MISIÓN', image.mission_id],
            ['TIMESTAMP', new Date(image.timestamp).toLocaleString()],
            ['LATITUD', image.lat.toFixed(6)],
            ['LONGITUD', image.lng.toFixed(6)],
            ['ALTITUD', `${image.altitude_m.toFixed(1)} m`],
            ['MODO', image.view_mode.toUpperCase()],
          ].map(([label, value]) => (
            <div key={label}>
              <SectionLabel>{label}</SectionLabel>
              <span style={{ color: C.text}}>{value}</span>
            </div>
          ))}
          <div style={{paddingTop: 18}}>
            <SectionLabel>DETECCIONES</SectionLabel>
            <span style={{ color: C.orange, fontWeight: 'bold', fontSize: 18 }}>{image.detection_count}</span>
          </div>
        </div>

        <button
          onClick={onClose}
          style={{
            marginTop: 16,
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
          onMouseEnter={e => { (e.target as HTMLElement).style.borderColor = C.orange; (e.target as HTMLElement).style.color = C.orange }}
          onMouseLeave={e => { (e.target as HTMLElement).style.borderColor = C.border; (e.target as HTMLElement).style.color = C.muted }}
        >
          ✕ CERRAR
        </button>
      </div>
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function GalleryPage({ initialMissionFilter = '' }: { initialMissionFilter?: string }) {
  const { images, total, loading, error, fetchImages, getFullImageUrl } = useImageGallery()
  const [selectedImage, setSelectedImage] = useState<ImageMeta | null>(null)
  const [missionFilter, setMissionFilter] = useState(initialMissionFilter)
  const [page, setPage] = useState(1)

  useEffect(() => {
    setMissionFilter(initialMissionFilter)
    setPage(1)
  }, [initialMissionFilter])
  const [view, setView] = useState<'grid' | 'map'>('grid')
  const gridRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetchImages({ mission_id: missionFilter || undefined, page })
  }, [missionFilter, page, fetchImages])

  const goToPage = (next: number) => setPage(next)

  const pageCount = Math.ceil(total / 20)

  const viewBtn = (active: boolean): React.CSSProperties => ({
    background: active ? C.orange : 'transparent',
    color: active ? '#fff' : C.muted,
    border: `1px solid ${active ? C.orange : C.border}`,
    borderRadius: 4,
    padding: '5px 16px',
    cursor: 'pointer',
    fontFamily: 'monospace',
    fontSize: 10,
    letterSpacing: 1.5,
    transition: 'all 0.15s',
    boxShadow: active ? `0 0 12px rgba(255,109,0,0.3)` : 'none',
  })

  const paginBtn = (disabled: boolean): React.CSSProperties => ({
    background: 'transparent',
    color: disabled ? C.textDim : C.muted,
    border: `1px solid ${disabled ? 'rgba(255,255,255,0.03)' : C.border}`,
    borderRadius: 4,
    padding: '6px 16px',
    cursor: disabled ? 'default' : 'pointer',
    fontFamily: 'monospace',
    fontSize: 10,
    letterSpacing: 1,
  })

  return (
    <div style={{
      background: C.bg,
      color: C.text,
      minHeight: '100%',
      position: 'relative' as const,
    }}>
      {/* Scanlines */}
      <div style={scanlineStyle} />

      {/* Subtle grid bg */}
      <div style={{
        position: 'fixed', inset: 0, zIndex: 0, pointerEvents: 'none',
        backgroundImage: `linear-gradient(${C.grid} 1px, transparent 1px), linear-gradient(90deg, ${C.grid} 1px, transparent 1px)`,
        backgroundSize: '40px 40px',
      }} />

      <div style={{ position: 'relative', zIndex: 1, padding: '24px 28px' }}>

        {/* Header */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-end',
          marginBottom: 24,
          paddingBottom: 20,
          borderBottom: `1px solid ${C.border}`,
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
              {/* Accent bar */}
              <div style={{ width: 3, height: 28, background: C.orange, borderRadius: 2 }} />
              <div style={{ fontFamily: 'monospace', fontSize: 22, fontWeight: 'bold', color: C.orange, letterSpacing: 1 }}>
                GALERÍA DE CAPTURAS
              </div>
            </div>
            <div style={{ fontFamily: 'monospace', fontSize: 10, color: C.muted, letterSpacing: 1.5, paddingLeft: 13 }}>
              Detecciones almacenadas · MongoDB
            </div>
          </div>

          <div style={{ display: 'flex', gap: 6 }}>
            <button style={viewBtn(view === 'grid')} onClick={() => setView('grid')}>▦ GRILLA</button>
            <button style={viewBtn(view === 'map')} onClick={() => setView('map')}>◎ MAPA</button>
          </div>
        </div>

        {/* Filters bar */}
        <div style={{
          display: 'flex',
          gap: 12,
          marginBottom: 24,
          alignItems: 'center',
          flexWrap: 'wrap' as const,
        }}>
          <div style={{ position: 'relative' as const }}>
            <span style={{
              position: 'absolute',
              left: 10, top: '50%', transform: 'translateY(-50%)',
              color: C.textDim, fontFamily: 'monospace', fontSize: 11, pointerEvents: 'none',
            }}>⌕</span>
            <input
              placeholder="Filtrar por misión..."
              value={missionFilter}
              onChange={e => { setMissionFilter(e.target.value); setPage(1) }}
              style={{
                background: C.panel,
                border: `1px solid ${C.border}`,
                color: C.text,
                borderRadius: 4,
                padding: '6px 10px 6px 28px',
                fontSize: 11,
                fontFamily: 'monospace',
                outline: 'none',
                width: 210,
                transition: 'border-color 0.15s',
              }}
              onFocus={e => (e.target.style.borderColor = C.orange)}
              onBlur={e => (e.target.style.borderColor = C.border)}
            />
          </div>

          {/* Stats pills */}
          <div style={{ marginLeft: 'auto', display: 'flex', gap: 8, alignItems: 'center' }}>
            <div style={{
              background: C.panel,
              border: `1px solid ${C.border}`,
              borderRadius: 4,
              padding: '5px 12px',
              fontFamily: 'monospace',
              fontSize: 10,
              color: C.muted,
              letterSpacing: 1,
            }}>
              <span style={{ color: C.orange, fontWeight: 'bold', marginRight: 6 }}>{total}</span>
              IMAGEN{total !== 1 ? 'ES' : ''}
            </div>
          </div>
        </div>

        {/* Loading indicator — solo un pill, no colapsa el contenido */}
        {loading && (
          <div style={{
            display: 'flex', alignItems: 'center', gap: 8,
            marginBottom: 12, fontFamily: 'monospace', fontSize: 10,
            color: C.muted, letterSpacing: 2,
          }}>
            <div style={{ width: 5, height: 5, borderRadius: '50%', background: C.orange }} />
            CARGANDO...
          </div>
        )}
        {error && (
          <p style={{
            fontFamily: 'monospace', fontSize: 11, color: '#ef4444',
            textAlign: 'center', marginTop: 40, letterSpacing: 1,
            background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)',
            borderRadius: 4, padding: '12px 20px',
          }}>
            ⚠ {error.toUpperCase()}
          </p>
        )}

        {/* Grid view — siempre visible, opacidad baja mientras carga */}
        {view === 'grid' && (
          <>
            {images.length === 0 && !loading && (
              <div style={{
                textAlign: 'center', padding: '80px 0',
                fontFamily: 'monospace', fontSize: 11, color: C.textDim, letterSpacing: 2,
              }}>
                <div style={{ fontSize: 32, marginBottom: 12, opacity: 0.3 }}>◎</div>
                SIN CAPTURAS ALMACENADAS
              </div>
            )}
            <div ref={gridRef} style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
              gap: 12,
              opacity: loading ? 0.4 : 1,
              transition: 'opacity 0.2s',
              pointerEvents: loading ? 'none' : 'auto',
            }}>
              {images.map(img => (
                <ImageCard key={img.id} image={img} onSelect={setSelectedImage} />
              ))}
            </div>
          </>
        )}

        {/* Map view */}
        {view === 'map' && images.length > 0 && (
          <div style={{
            borderRadius: 6,
            overflow: 'hidden',
            border: `1px solid ${C.border}`,
            boxShadow: '0 0 30px rgba(0,0,0,0.5)',
          }}>
            <MapContainer
              center={[images[0].lat, images[0].lng]}
              zoom={15}
              style={{ height: '65vh' }}
            >
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='&copy; OpenStreetMap contributors'
              />
              {images.map(img => (
                <Marker key={img.id} position={[img.lat, img.lng]} icon={dotIcon()}>
                  <Popup>
                    <img
                      src={`data:image/jpeg;base64,${img.thumbnail_b64}`}
                      alt="thumb"
                      style={{ width: 160, display: 'block', marginBottom: 6, borderRadius: 3 }}
                    />
                    <div style={{ fontSize: 11, fontFamily: 'monospace' }}>
                      <div>{new Date(img.timestamp).toLocaleString()}</div>
                      <div style={{ color: '#FF6D00', marginTop: 2, fontWeight: 'bold' }}>
                        {img.detection_count} detección(es)
                      </div>
                      <button
                        onClick={() => setSelectedImage(img)}
                        style={{ marginTop: 6, fontSize: 10, cursor: 'pointer', fontFamily: 'monospace' }}
                      >
                        VER COMPLETA →
                      </button>
                    </div>
                  </Popup>
                </Marker>
              ))}
            </MapContainer>
          </div>
        )}

        {view === 'map' && !loading && images.length === 0 && (
          <div style={{
            textAlign: 'center', padding: '80px 0',
            fontFamily: 'monospace', fontSize: 11, color: C.textDim, letterSpacing: 2,
          }}>
            <div style={{ fontSize: 32, marginBottom: 12, opacity: 0.3 }}>◎</div>
            SIN CAPTURAS PARA MOSTRAR
          </div>
        )}

        {/* Pagination */}
        {pageCount > 1 && (
          <div style={{
            display: 'flex', gap: 8, marginTop: 28,
            justifyContent: 'center', alignItems: 'center', color: C.orange
          }}>
            <button
              type="button"
              disabled={page === 1}
              onClick={() => goToPage(page - 1)}
              style={{ ...paginBtn(page === 1), fontSize: 14 }} 
            >
              ← ANT
            </button>

            {/* Pill de página */}
            <div style={{
              display: 'flex', alignItems: 'center', gap: 6,
              background: C.panel,
              border: `1px solid ${C.border}`,
              borderRadius: 4,
              padding: '5px 14px',
              fontFamily: 'monospace',
              fontSize: 12,
              letterSpacing: 1.5,
            }}>
              <span style={{ color: C.textDim }}>PÁG</span>
              <span style={{
                color: C.orange,
                fontWeight: 'bold',
                fontSize: 16,
              }}>{page}</span>
              <span style={{ color: C.textDim }}>DE</span>
              <span style={{ color: C.muted, fontSize: 16 }}>{pageCount}</span>
            </div>
            <button
              type="button"
              disabled={page === pageCount}
              onClick={() => goToPage(page + 1)}
              style={{...paginBtn(page === pageCount), fontSize: 14 }}
            >
              SIG →
            </button>
          </div>
        )}
      </div>

      {/* Modal */}
      {selectedImage && (
        <ImageModal
          image={selectedImage}
          fullUrl={getFullImageUrl(selectedImage.id)}
          onClose={() => setSelectedImage(null)}
        />
      )}
    </div>
  )
}