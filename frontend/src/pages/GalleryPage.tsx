import { useEffect, useState } from 'react'
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import L from 'leaflet'
import { useImageGallery } from '../hooks/useImageGallery'
import type { ImageMeta } from '../types'
import 'leaflet/dist/leaflet.css'

// ── Helpers ───────────────────────────────────────────────────────────────────

function dotIcon(color: string) {
  return L.divIcon({
    className: '',
    html: `<div style="
      width:14px;height:14px;border-radius:50%;
      background:${color};border:2px solid #fff;
      box-shadow:0 0 4px rgba(0,0,0,0.5);
    "></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  })
}

// ── Sub-components ────────────────────────────────────────────────────────────

function ImageCard({
  image,
  onSelect,
}: {
  image: ImageMeta
  onSelect: (img: ImageMeta) => void
}) {
  return (
    <div
      onClick={() => onSelect(image)}
      style={{
        cursor: 'pointer',
        border: '1px solid #334155',
        borderRadius: 8,
        overflow: 'hidden',
        background: '#1e293b',
        transition: 'border-color 0.15s',
      }}
      onMouseEnter={e => (e.currentTarget.style.borderColor = '#3b82f6')}
      onMouseLeave={e => (e.currentTarget.style.borderColor = '#334155')}
    >
      <div style={{ position: 'relative' }}>
        <img
          src={`data:image/jpeg;base64,${image.thumbnail_b64}`}
          alt="captura"
          style={{ width: '100%', display: 'block' }}
        />
        {image.has_detections && (
          <span
            style={{
              position: 'absolute', top: 6, right: 6,
              background: '#ef4444', color: '#fff',
              borderRadius: 12, padding: '2px 8px',
              fontSize: 11, fontWeight: 700,
            }}
          >
            {image.detection_count} det.
          </span>
        )}
      </div>
      <div style={{ padding: '8px 10px', fontSize: 12, color: '#94a3b8' }}>
        <div style={{ color: '#cbd5e1', marginBottom: 2 }}>
          {new Date(image.timestamp).toLocaleString()}
        </div>
        <div>{image.lat.toFixed(5)}, {image.lng.toFixed(5)}</div>
        <div style={{ color: '#64748b', marginTop: 2 }}>
          {image.altitude_m.toFixed(1)} m · {image.view_mode.toUpperCase()}
        </div>
      </div>
    </div>
  )
}

function ImageModal({
  image,
  fullUrl,
  onClose,
}: {
  image: ImageMeta
  fullUrl: string
  onClose: () => void
}) {
  return (
    <div
      style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.85)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        zIndex: 9999,
      }}
      onClick={onClose}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{
          background: '#0f172a', borderRadius: 12, padding: 24,
          maxWidth: 720, width: '90vw', maxHeight: '90vh', overflowY: 'auto',
        }}
      >
        <img
          src={fullUrl}
          alt="imagen completa"
          style={{ width: '100%', borderRadius: 8, display: 'block' }}
        />
        <div style={{ marginTop: 16, color: '#cbd5e1', fontSize: 14, lineHeight: 1.7 }}>
          <p><strong>Misión:</strong> {image.mission_id}</p>
          <p><strong>Timestamp:</strong> {new Date(image.timestamp).toLocaleString()}</p>
          <p><strong>Coordenadas:</strong> {image.lat.toFixed(6)}, {image.lng.toFixed(6)}</p>
          <p><strong>Altitud:</strong> {image.altitude_m.toFixed(1)} m</p>
          <p><strong>Modo cámara:</strong> {image.view_mode}</p>
          <p><strong>Detecciones:</strong> {image.detection_count}</p>
        </div>
        <button
          onClick={onClose}
          style={{
            marginTop: 16, background: '#334155', color: '#fff',
            border: 'none', borderRadius: 6, padding: '8px 20px', cursor: 'pointer',
          }}
        >
          Cerrar
        </button>
      </div>
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function GalleryPage() {
  const { images, total, loading, error, fetchImages, getFullImageUrl } = useImageGallery()
  const [selectedImage, setSelectedImage] = useState<ImageMeta | null>(null)
  const [missionFilter, setMissionFilter] = useState('')
  const [onlyDetections, setOnlyDetections] = useState(false)
  const [page, setPage] = useState(1)
  const [view, setView] = useState<'grid' | 'map'>('grid')

  useEffect(() => {
    fetchImages({
      mission_id: missionFilter || undefined,
      has_detections: onlyDetections || undefined,
      page,
    })
  }, [missionFilter, onlyDetections, page, fetchImages])

  const pageCount = Math.ceil(total / 20)

  const tabBtn = (active: boolean) => ({
    background: active ? '#3b82f6' : '#1e293b',
    color: '#fff' as const,
    border: 'none',
    borderRadius: 6,
    padding: '6px 16px',
    cursor: 'pointer' as const,
  })

  return (
    <div style={{ background: '#0f172a', color: '#e2e8f0', padding: 24 }}>

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700 }}>Galería de Capturas</h1>
        <div style={{ display: 'flex', gap: 8 }}>
          <button style={tabBtn(view === 'grid')} onClick={() => setView('grid')}>Grilla</button>
          <button style={tabBtn(view === 'map')} onClick={() => setView('map')}>Mapa</button>
        </div>
      </div>

      {/* Filtros */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap', alignItems: 'center' }}>
        <input
          placeholder="ID de misión..."
          value={missionFilter}
          onChange={e => { setMissionFilter(e.target.value); setPage(1) }}
          style={{
            background: '#1e293b', border: '1px solid #334155',
            color: '#e2e8f0', borderRadius: 6, padding: '6px 12px', fontSize: 14,
          }}
        />
        <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 14, cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={onlyDetections}
            onChange={e => { setOnlyDetections(e.target.checked); setPage(1) }}
          />
          Solo con detecciones
        </label>
        <span style={{ marginLeft: 'auto', color: '#64748b', fontSize: 13 }}>
          {total} imagen{total !== 1 ? 'es' : ''}
        </span>
      </div>

      {loading && <p style={{ color: '#64748b' }}>Cargando...</p>}
      {error   && <p style={{ color: '#ef4444' }}>{error}</p>}

      {/* Vista grilla */}
      {view === 'grid' && !loading && (
        <>
          {images.length === 0 && (
            <p style={{ color: '#64748b', textAlign: 'center', marginTop: 60 }}>
              No hay imágenes guardadas aún.
            </p>
          )}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
            gap: 12,
          }}>
            {images.map(img => (
              <ImageCard key={img.id} image={img} onSelect={setSelectedImage} />
            ))}
          </div>
        </>
      )}

      {/* Vista mapa */}
      {view === 'map' && images.length > 0 && (
        <MapContainer
          center={[images[0].lat, images[0].lng]}
          zoom={15}
          style={{ height: '65vh', borderRadius: 10 }}
        >
          <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          {images.map(img => (
            <Marker
              key={img.id}
              position={[img.lat, img.lng]}
              icon={dotIcon(img.has_detections ? '#ef4444' : '#3b82f6')}
            >
              <Popup>
                <img
                  src={`data:image/jpeg;base64,${img.thumbnail_b64}`}
                  alt="thumb"
                  style={{ width: 160, display: 'block', marginBottom: 6 }}
                />
                <div style={{ fontSize: 12 }}>
                  <div>{new Date(img.timestamp).toLocaleString()}</div>
                  <div>{img.detection_count} detección(es)</div>
                  <button
                    onClick={() => setSelectedImage(img)}
                    style={{ marginTop: 6, fontSize: 11, cursor: 'pointer' }}
                  >
                    Ver completa
                  </button>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      )}

      {view === 'map' && images.length === 0 && !loading && (
        <p style={{ color: '#64748b', textAlign: 'center', marginTop: 60 }}>
          No hay imágenes para mostrar en el mapa.
        </p>
      )}

      {/* Paginación */}
      {pageCount > 1 && (
        <div style={{ display: 'flex', gap: 8, marginTop: 20, justifyContent: 'center', alignItems: 'center' }}>
          <button
            disabled={page === 1}
            onClick={() => setPage(p => p - 1)}
            style={{ background: '#1e293b', color: '#fff', border: '1px solid #334155', borderRadius: 6, padding: '6px 14px', cursor: 'pointer' }}
          >
            ← Anterior
          </button>
          <span style={{ padding: '6px 12px', color: '#94a3b8', fontSize: 13 }}>
            {page} / {pageCount}
          </span>
          <button
            disabled={page === pageCount}
            onClick={() => setPage(p => p + 1)}
            style={{ background: '#1e293b', color: '#fff', border: '1px solid #334155', borderRadius: 6, padding: '6px 14px', cursor: 'pointer' }}
          >
            Siguiente →
          </button>
        </div>
      )}

      {/* Modal imagen completa */}
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
