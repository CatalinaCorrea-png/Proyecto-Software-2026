import { MapContainer, TileLayer, Marker, Popup, Polyline, Circle, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { CoverageGrid } from './CoverageGrid'          // ← nuevo
import { useSearchGrid } from '../../hooks/useSearchGrid'  // ← nuevo
import type { DroneTelemetry, Detection } from '../../types'
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
      width: 18px; height: 18px;
      background: ${color};
      border: 3px solid white;
      border-radius: 50%;
      box-shadow: 0 0 8px ${color}, 0 0 16px ${color};
    "></div>`,
    iconSize: [18, 18],
    iconAnchor: [9, 9],
  })
}

interface SearchMapProps {
  telemetry: DroneTelemetry | null
  detections: Detection[]
  trail: Array<{ lat: number; lng: number }>
}

const DEFAULT_CENTER = { lat: -34.6083, lng: -58.3712 }

// Componente para centrar el mapa en la posición inicial del drone
function InitialCenter({ position }: { position: [number, number] }) {
  const map = useMap()
  const centeredRef = useRef(false)

  useEffect(() => {
    // Solo centrar la primera vez que llega una posición válida
    if (!centeredRef.current && position[0] !== 0 && position[1] !== 0) {
      map.setView(position, 16)
      centeredRef.current = true  // nunca más
    }
  }, [position, map])

  return null
}

export function SearchMap({ telemetry, detections, trail }: SearchMapProps) {
  const center = telemetry?.position ?? DEFAULT_CENTER
  const { cells, coverage } = useSearchGrid('ws://localhost:8000/ws/grid')  // ← grilla de cobertura

  return (
    <div style={{ position: 'relative', height: '100%' }}>
      {/* Badge de cobertura sobre el mapa */}
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

        {/* Componente para centrar el mapa en la posición inicial del drone */}
        {telemetry && (<InitialCenter position={[telemetry.position.lat, telemetry.position.lng]}/>)}

        {/* Grilla de cobertura */}
        <CoverageGrid cells={cells} />

        {trail.length > 1 && (
          <Polyline
            positions={trail.map(p => [p.lat, p.lng])}
            color="#00BCD4" 
            weight={2} 
            opacity={0.6}
            smoothFactor={3}   // ← simplifica puntos cercanos
          />
        )}

        {telemetry && (
          <Marker
            position={[telemetry.position.lat, telemetry.position.lng]}
            icon={droneIcon}
          >
            <Popup>
              <strong>Drone</strong><br />
              Batería: {telemetry.battery}%<br />
              Altitud: {telemetry.position.altitude}m
            </Popup>
          </Marker>
        )}

        {/* Primero los círculos (quedan abajo) */}
        {detections.map(det => {
          const color = det.confidence === 'high' ? '#00C853'
            : det.confidence === 'medium' ? '#FFD600'
            : '#FF5252'
          return (
            <Circle
              key={`circle-${det.id}`}
              center={[det.position.lat, det.position.lng]}
              radius={15}
              pathOptions={{
                color,
                fillColor: color,
                fillOpacity: 0.15,
                weight: 1.5
              }}
            />
          )
        })}

        {/* Después los marcadores (quedan encima) */}
        {detections.map(det => (
          <Marker
            key={`marker-${det.id}`}
            position={[det.position.lat, det.position.lng]}
            icon={detectionIcon(det.confidence)}
          >
            <Popup>
              <strong>Detección {det.confidence}</strong><br />
              Fuente: {det.source}<br />
              {det.temperature && <>Temp: {det.temperature}°C<br /></>}
              {new Date(det.timestamp).toLocaleTimeString()}
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  )
}