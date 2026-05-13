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
  onNewDetection: (detection: Detection) => void
}

export function Dashboard({
  isConnected,
  telemetry,
  trail,
  mapDetections,
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
      gridTemplateColumns: '1fr .5fr .5fr',
      gridTemplateRows: '1fr',
      width: '100%',
      height: '100%',
      overflow: 'hidden',
      background: '#0A0E1A',
      gap: 10,
      padding: 10,
    }}>

      {/* ── Mapa — ocupa todo el alto ── */}
      <SearchMap
        telemetry={telemetry}
        detections={mapDetections}
        trail={trail}
        savedImages={images}
        onImageClick={setSelectedImage}
      />

      {/* ── Panel telemetria, camara y control ── */}
      <div style={{
        display: 'grid',
        gridTemplateRows: 'auto auto auto auto',
        gap: 6,
        alignContent: 'start',
        overflowY: 'auto',
        minHeight: 0,
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
          detectionCount={mapDetections.length}
        />

        {/* Cámara */}
        <CameraFeed onNewDetection={onNewDetection} />

        {/* Control de vuelo */}
        <DroneController />

      </div>

      {/* ── Panel alertas ── */}
      <div style={{
        display: 'grid',
        gridTemplateRows: 'auto',
        gap: 10,
        alignContent: 'center',
        overflowY: 'auto',
        minHeight: 0,
      }}>
        <DetectionAlert detections={mapDetections} />
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
