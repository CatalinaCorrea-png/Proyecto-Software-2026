import { MapContainer, TileLayer, Marker, Popup, Polyline, Circle, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { CoverageGrid } from './CoverageGrid'
import { useSearchGrid } from '../../hooks/useSearchGrid'
import { WS } from '../../config'
import type { DroneTelemetry, Detection, ImageMeta } from '../../types'
import { useEffect, useRef } from 'react'

delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

const droneIcon = L.divIcon({
  className: '',
  html: `<div style="width:20px;height:20px;background:#FF6D00;border:2px solid white;border-radius:50%;box-shadow:0 0 8px #FF6D00"></div>`,
  iconSize: [20, 20], iconAnchor: [10, 10],
})


const detectionIcon = (confidence: Detection['confidence']) => {
  const color = confidence === 'high' ? '#00C853'
    : confidence === 'medium' ? '#FFD600'
    : '#FF5252'
  return L.divIcon({
    className: '',
    html: `<div style="
      width:18px;height:18px;
      background:${color};border:3px solid white;border-radius:50%;
      box-shadow:0 0 8px ${color},0 0 16px ${color};
    "></div>`,
    iconSize: [18, 18],
    iconAnchor: [9, 9],
  })
}


interface SearchMapProps {
  telemetry: DroneTelemetry | null
  detections: Detection[]
  trail: Array<{ lat: number; lng: number }>
  savedImages?: ImageMeta[]
  onImageClick?: (img: ImageMeta) => void
}

const DEFAULT_CENTER = { lat: -34.6083, lng: -58.3712 }

function AutoCenter({ position }: { position: [number, number] }) {
  const map = useMap()
  const lastRef = useRef<string>('')

  useEffect(() => {
    if (position[0] === 0 && position[1] === 0) return
    const key = `${position[0].toFixed(3)},${position[1].toFixed(3)}`
    if (key !== lastRef.current) {
      map.setView(position, 16)
      lastRef.current = key
    }
  }, [position, map])

  return null
}

function closestImage(det: Detection, imgs: ImageMeta[]): ImageMeta | undefined {
  let best: ImageMeta | undefined
  let minD = Infinity
  for (const img of imgs) {
    const d = Math.abs(img.lat - det.position.lat) + Math.abs(img.lng - det.position.lng)
    if (d < minD) { minD = d; best = img }
  }
  return minD < 0.001 ? best : undefined   // ~100 m de tolerancia
}

export function SearchMap({ telemetry, detections, trail, savedImages = [], onImageClick }: SearchMapProps) {
  const center = telemetry?.position ?? DEFAULT_CENTER
  const { cells, coverage } = useSearchGrid(`${WS}/ws/grid`)

  return (
    <div style={{ position: 'relative', height: '100%' }}>
      {/* Badge de cobertura */}
      <div style={{
        position: 'absolute', top: 12, right: 12, zIndex: 1000,
        background: '#0D1B2A', border: '1px solid #1E3A5F',
        borderRadius: 6, padding: '6px 12px',
        fontFamily: 'monospace', color: 'white', fontSize: 13
      }}>
        <span style={{ color: '#78909C' }}>COBERTURA </span>
        <span style={{ color: '#00BCD4', fontWeight: 'bold' }}>{coverage}%</span>
      </div>

      <MapContainer
        center={[center.lat, center.lng]}
        zoom={13}
        style={{ height: '100%', width: '100%', borderRadius: '8px' }}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution="© OpenStreetMap"
        />

        {telemetry && <AutoCenter position={[telemetry.position.lat, telemetry.position.lng]} />}

        <CoverageGrid cells={cells} />

        {trail.length > 1 && (
          <Polyline
            positions={trail.map(p => [p.lat, p.lng])}
            color="#00BCD4"
            weight={2}
            opacity={0.6}
            smoothFactor={3}
          />
        )}

        {telemetry && (
          <Marker position={[telemetry.position.lat, telemetry.position.lng]} icon={droneIcon}>
            <Popup>
              <strong>Drone</strong><br />
              Batería: {telemetry.battery}%<br />
              Altitud: {telemetry.position.altitude}m
            </Popup>
          </Marker>
        )}

        {/* Círculo de fondo para cada detección */}
        {detections.map(det => {
          const color = det.confidence === 'high' ? '#00C853'
            : det.confidence === 'medium' ? '#FFD600'
            : '#FF5252'
          return (
            <Circle
              key={`circle-${det.id}`}
              center={[det.position.lat, det.position.lng]}
              radius={15}
              pathOptions={{ color, fillColor: color, fillOpacity: 0.15, weight: 1.5 }}
            />
          )
        })}

        {/* Marcador de detección con popup de imagen guardada */}
        {detections.map(det => {
          const img = closestImage(det, savedImages)
          return (
            <Marker
              key={`marker-${det.id}`}
              position={[det.position.lat, det.position.lng]}
              icon={detectionIcon(det.confidence)}
            >
              <Popup>
                {img ? (
                  <>
                    <img
                      src={`data:image/jpeg;base64,${img.thumbnail_b64}`}
                      alt="captura"
                      style={{ width: 170, display: 'block', marginBottom: 8, borderRadius: 3 }}
                    />
                    <div style={{ fontFamily: 'monospace', fontSize: 11 }}>
                      <div style={{ marginBottom: 3 }}>{new Date(img.timestamp).toLocaleString()}</div>
                      <div style={{ color: '#FF6D00', fontWeight: 'bold', marginBottom: 3 }}>
                        {img.detection_count} detección(es)
                      </div>
                      <div style={{ color: '#78909C', marginBottom: 8 }}>
                        Alt: {img.altitude_m.toFixed(1)} m
                      </div>
                      {onImageClick && (
                        <button
                          onClick={() => onImageClick(img)}
                          style={{
                            background: '#FF6D00', color: '#fff',
                            border: 'none', borderRadius: 3,
                            padding: '4px 10px', cursor: 'pointer',
                            fontFamily: 'monospace', fontSize: 10,
                            letterSpacing: 1, width: '100%',
                          }}
                        >
                          VER COMPLETA →
                        </button>
                      )}
                    </div>
                  </>
                ) : (
                  <div style={{ fontFamily: 'monospace', fontSize: 11 }}>
                    <div style={{ fontWeight: 'bold', marginBottom: 4 }}>
                      Detección {det.confidence}
                    </div>
                    <div style={{ color: '#78909C' }}>Fuente: {det.source}</div>
                    {det.temperature && (
                      <div style={{ color: '#78909C' }}>Temp: {det.temperature}°C</div>
                    )}
                    <div style={{ color: '#78909C' }}>
                      {new Date(det.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                )}
              </Popup>
            </Marker>
          )
        })}
      </MapContainer>
    </div>
  )
}
