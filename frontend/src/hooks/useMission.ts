import { useState, useEffect } from 'react'
import type { DroneTelemetry, Detection, WsMessage } from '../types'

interface MissionState {
  telemetry: DroneTelemetry | null
  detections: Detection[]
  trail: Array<{ lat: number; lng: number }>  // rastro del drone
}

export function useMission(lastMessage: WsMessage | null): MissionState {
  const [telemetry, setTelemetry] = useState<DroneTelemetry | null>(null)
  const [detections, setDetections] = useState<Detection[]>([])
  const [trail, setTrail] = useState<Array<{ lat: number; lng: number }>>([])

  useEffect(() => {
    if (!lastMessage) return

    // Según el tipo de mensaje, actualiza el estado correspondiente
    if (lastMessage.type === 'telemetry') {
      setTelemetry(lastMessage.data)
      setTrail(prev => { // agrega punto al rastro
        const newPoint = {
          lat: lastMessage.data.position.lat,
          lng: lastMessage.data.position.lng
        }
        // Máximo 200 puntos en el rastro
        const updated = [...prev, newPoint]
        return updated.length > 200 ? updated.slice(-200) : updated
      })
    }

    if (lastMessage.type === 'detection') {
       if (lastMessage.data.confidence === 'low') return // ignora detecciones de baja confianza
      setDetections(prev => [lastMessage.data, ...prev].slice(0, 50)) // agrega al principio
    }
  }, [lastMessage]) // ← se ejecuta cada vez que lastMessage cambia
  //                       o sea, cada vez que llega un mensaje nuevo

  return { telemetry, detections, trail }
}