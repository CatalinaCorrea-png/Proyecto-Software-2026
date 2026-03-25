import { MapContainer, TileLayer, Marker, Popup, Polyline, Circle } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import type { DroneTelemetry, Detection } from '../../types'

// Fix icono default de Leaflet (bug conocido con Vite)
delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

// Icono del drone (naranja)
const droneIcon = L.divIcon({
  className: '',
  html: `<div style="
    width: 20px; height: 20px;
    background: #FF6D00;
    border: 2px solid white;
    border-radius: 50%;
    box-shadow: 0 0 8px #FF6D00;
  "></div>`,
  iconSize: [20, 20],
  iconAnchor: [10, 10],
})

// Icono de detección según confianza
const detectionIcon = (confidence: Detection['confidence']) => {
  const color = confidence === 'high' ? '#00C853'
    : confidence === 'medium' ? '#FFD600'
    : '#FF5252'
  return L.divIcon({
    className: '',
    html: `<div style="
      width: 14px; height: 14px;
      background: ${color};
      border: 2px solid white;
      border-radius: 50%;
      box-shadow: 0 0 6px ${color};
    "></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  })
}

interface SearchMapProps {
  telemetry: DroneTelemetry | null
  detections: Detection[]
  trail: Array<{ lat: number; lng: number }>
}

const DEFAULT_CENTER = { lat: -34.6083, lng: -58.3712 }

export function SearchMap({ telemetry, detections, trail }: SearchMapProps) {
  const center = telemetry?.position ?? DEFAULT_CENTER

  return (
    <MapContainer
      center={[center.lat, center.lng]}
      zoom={16}
      style={{ height: '100%', width: '100%', borderRadius: '8px' }}
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution="© OpenStreetMap"
      />

      {/* Rastro del drone */}
      {trail.length > 1 && (
        <Polyline
          positions={trail.map(p => [p.lat, p.lng])}
          color="#00BCD4"
          weight={2}
          opacity={0.6}
        />
      )}

      {/* Posición actual del drone */}
      {telemetry && (
        <Marker
          position={[telemetry.position.lat, telemetry.position.lng]}
          icon={droneIcon}
        >
          <Popup>
            <strong>Drone</strong><br />
            Batería: {telemetry.battery}%<br />
            Altitud: {telemetry.position.altitude}m<br />
            Estado: {telemetry.status}
          </Popup>
        </Marker>
      )}

      {/* Detecciones */}
      {detections.map(det => (
        <div key={det.id}>
          <Marker
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
          <Circle
            center={[det.position.lat, det.position.lng]}
            radius={8}
            color={det.confidence === 'high' ? '#00C853' : det.confidence === 'medium' ? '#FFD600' : '#FF5252'}
            fillOpacity={0.1}
          />
        </div>
      ))}
    </MapContainer>
  )
}