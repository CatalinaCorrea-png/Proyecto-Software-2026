// Posición GPS
export interface GpsPosition {
  lat: number
  lng: number
  altitude: number
  timestamp: number // Cuando se capturó, no cuando se procesó
}

// Estado del drone
export interface DroneTelemetry {
  position: GpsPosition
  battery: number        // porcentaje 0-100
  status: 'idle' | 'flying' | 'hover' | 'returning' | 'landed'
  speed: number          // m/s
  elapsed: number
  source?: 'hardware' | 'sim'
}

// Una detección de persona
export interface Detection {
  id: string
  position: GpsPosition
  confidence: 'high' | 'medium' | 'low'
  source: 'rgb' | 'thermal' | 'fusion'
  temperature?: number   // si viene de térmica
  timestamp: number
  imageUrl?: string      // captura del momento
}

// Celda del mapa de cobertura
export interface GridCell {
  row: number
  col: number
  status: 'unexplored' | 'explored' | 'detection'
  lat: number
  lng: number
}

// Misión completa
export interface Mission {
  id: string
  name: string
  status: 'pending' | 'active' | 'completed' | 'aborted'
  area: GpsPosition[]    // polígono del área de búsqueda
  startTime?: number
  endTime?: number
  detections: Detection[]
  grid: GridCell[]
}

// Mensajes que llegan por WebSocket desde el backend
export type WsMessage =
  | { type: 'telemetry'; data: DroneTelemetry }
  | { type: 'detection'; data: Detection }
  | { type: 'grid_update'; data: GridCell }
  | { type: 'mission_status'; data: { status: Mission['status'] } }

// Imagen capturada almacenada en MongoDB
export interface ImageMeta {
  id: string
  mission_id: string
  timestamp: string
  lat: number
  lng: number
  altitude_m: number
  view_mode: 'rgb' | 'thermal' | 'overlay'
  has_detections: boolean
  detection_count: number
  thumbnail_b64: string
  detection_ids: string[]
}

export interface ImageListResponse {
  items: ImageMeta[]
  total: number
  page: number
  page_size: number
}