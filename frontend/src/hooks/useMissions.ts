import { useState, useEffect } from 'react'

export interface Mission {
  id: number
  created_at: string
  started_at: string | null
  ended_at: string | null
  status: string
  initial_battery: number
  final_battery: number | null
  coverage_percent: number | null
  detections_count: number
  grid_rows: number
  grid_cols: number
  grid_center_lat: number
  grid_center_lng: number
}

export interface MissionDetection {
  id: string
  timestamp: string
  position_lat: number
  position_lng: number
  position_altitude: number
  confidence: 'high' | 'medium'
  source: 'fusion' | 'rgb' | 'thermal'
  temperature: number | null
  rgb_confidence: number | null
}

export interface MissionDetail extends Mission {
  detections: MissionDetection[]
}

export function useMissions() {
  const [missions, setMissions] = useState<Mission[]>([])
  const [loading, setLoading] = useState(true)

  const fetchMissions = async () => {
    setLoading(true)
    try {
      const res = await fetch('http://localhost:8000/missions')
      setMissions(await res.json())
    } catch (e) {
      console.error('Error fetching missions:', e)
    } finally {
      setLoading(false)
    }
  }

  const fetchDetail = async (id: number): Promise<MissionDetail | null> => {
    try {
      const res = await fetch(`http://localhost:8000/missions/${id}`)
      return await res.json()
    } catch {
      return null
    }
  }

  useEffect(() => {
    fetchMissions()
  }, [])

  // Refresco automático mientras haya alguna misión activa
  useEffect(() => {
    const hasActive = missions.some(m => m.status === 'active')
    if (!hasActive) return
    const id = setInterval(fetchMissions, 10_000)
    return () => clearInterval(id)
  }, [missions])

  return { missions, loading, refetch: fetchMissions, fetchDetail }
}
