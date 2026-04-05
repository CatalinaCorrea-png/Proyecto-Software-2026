import { useEffect, useRef, useState } from 'react'
import type { FramePayload } from '../components/drone/CameraFeed'
import type { Detection } from '../types'
// import type { Metrics } from '../components/drone/PerformancePanel'

// interface FramePayload {
//   type: 'frame'
//   frame: string
//   thermal_overlay: string 
//   thermal_frame: string
//   fused_detections: Array<{
//     confidence: 'high' | 'medium' | 'low'
//     source: string
//     temperature?: number
//   }>
//   detection_count: number
//   metrics: Metrics
// }

interface DetectionEvent {
  type: 'detection'
  data: Detection
}

type DetectionMessage = FramePayload | DetectionEvent

interface UseDetectionFeedReturn {
  framePayload: FramePayload | null
  detections: Detection[]          // acumuladas para el mapa
  isConnected: boolean
}

export function useDetectionFeed(url: string): UseDetectionFeedReturn {
  const [framePayload, setFramePayload] = useState<FramePayload | null>(null)
  const [detections, setDetections] = useState<Detection[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    const connect = () => {
      const ws = new WebSocket(url)

      ws.onopen = () => setIsConnected(true)
      ws.onclose = () => {
        setIsConnected(false)
        setTimeout(connect, 2000) // se llama a sí misma recursivamente 
      }

      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data as string) as DetectionMessage

        if (msg.type === 'frame') {
          setFramePayload(msg)
        }

        if (msg.type === 'detection') {
          // Acumular en la lista para el mapa — máximo 100
          setDetections(prev => [msg.data, ...prev].slice(0, 100))
        }
      }

      wsRef.current = ws
    }

    connect()
    return () => wsRef.current?.close()
  }, [url])

  return { framePayload, detections, isConnected }
}