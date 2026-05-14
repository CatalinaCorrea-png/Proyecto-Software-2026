import { useEffect, useState } from 'react'
import { SearchMap } from '../components/map/SearchMap'
import { TelemetryPanel } from '../components/drone/TelemetryPanel'
import { DetectionAlert } from '../components/alerts/DetectionAlert'
import { CameraFeed } from '../components/drone/CameraFeed'
import { DroneController } from '../components/drone/DroneController'
import { ImageDetailModal } from '../components/ImageDetailModal'
import { useImageGallery } from '../hooks/useImageGallery'
import type { Detection, DroneTelemetry, ImageMeta, WsMessage } from '../types'

interface DashboardProps {
  lastMessage: WsMessage | null
  isConnected: boolean
  telemetry: DroneTelemetry | null
  trail: Array<{ lat: number; lng: number }>
  mapDetections: Detection[]
  detectionCount: number
  onNewDetection: (detection: Detection) => void
}

export function Dashboard({
  isConnected,
  telemetry,
  trail,
  mapDetections,
  detectionCount,
  onNewDetection,
}: DashboardProps) {
  const { images, fetchImages, getFullImageUrl } = useImageGallery()
  const [selectedImage, setSelectedImage] = useState<ImageMeta | null>(null)

  // Carga inicial de imágenes guardadas
  useEffect(() => {
    fetchImages({ page_size: 200 })
  }, [fetchImages])

  // Re-fetch 2 s después de cada nueva detección para dar tiempo al guardado en MongoDB
  useEffect(() => {
    if (mapDetections.length === 0) return
    const t = setTimeout(() => fetchImages({ page_size: 200 }), 2000)
    return () => clearTimeout(t)
  }, [mapDetections.length, fetchImages])

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '1fr 0.45fr 0.35fr',
      gridTemplateRows: '100vh',
      width: '100vw',
      height: '100vh',
      overflow: 'hidden',
      background: '#0A0E1A',
      gap: 6,
      padding: 6,
    }}>

      {/* ── Mapa — ocupa todo el alto ── */}
      <SearchMap
        telemetry={telemetry}
        detections={mapDetections}
        trail={trail}
        savedImages={images}
        onImageClick={setSelectedImage}
      />

      {/* ── Panel misión: telemetría + cámara ── */}
      <div style={{
        display: 'grid',
        gridTemplateRows: 'auto auto auto auto',
        gap: 6,
        alignContent: 'start',
        minHeight: 0,
        overflowY: 'auto',
      }}>

        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontFamily: 'monospace' }}>
          <div style={{ fontSize: 15, fontWeight: 'bold', color: '#FF6D00' }}>AeroSearch AI</div>
          <div style={{ fontSize: 10, color: '#78909C' }}>· búsqueda y rescate</div>
        </div>

        {/* Telemetría */}
        <TelemetryPanel
          telemetry={telemetry}
          isConnected={isConnected}
          detectionCount={detectionCount}
        />

        {/* Cámara */}
        <CameraFeed onNewDetection={onNewDetection} />

      </div>

      {/* ── Panel alertas + control de vuelo ── */}
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 6,
        minHeight: 0,
        overflow: 'hidden',
      }}>

        {/* Alertas — ocupa el espacio disponible */}
        <div style={{ flex: 1, minHeight: 0 }}>
          <DetectionAlert detections={mapDetections} />
        </div>

        {/* Control de vuelo — tamaño fijo abajo */}
        <DroneController droneStatus={telemetry?.status} />

      </div>

      {/* Modal al hacer clic en un punto naranja del mapa */}
      {selectedImage && (
        <ImageDetailModal
          image={selectedImage}
          fullUrl={getFullImageUrl(selectedImage.id)}
          onClose={() => setSelectedImage(null)}
        />
      )}

    </div>
  )
}
