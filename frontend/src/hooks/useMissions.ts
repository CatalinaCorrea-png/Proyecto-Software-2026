import { useState, useEffect } from 'react'
import { authFetch, authHeaders } from '../utils/authFetch'

export interface Mission {
  id: number
  name: string | null
  created_at: string
  started_at: string | null
  ended_at: string | null
  status: string
  initial_battery: number
  final_battery: number | null
  coverage_percent: number | null
  detections_count: number
  altitude: number | null
  cell_size_m: number | null
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

  const fetchMissions = async (showSpinner = false) => {
    if (showSpinner) setLoading(true)
    try {
      const res = await authFetch('/missions')
      setMissions(await res.json())
    } catch (e) {
      console.error('Error fetching missions:', e)
    } finally {
      if (showSpinner) setLoading(false)
    }
  }

  const fetchDetail = async (id: number): Promise<MissionDetail | null> => {
    try {
      const res = await authFetch(`/missions/${id}`)
      return await res.json()
    } catch {
      return null
    }
  }

  const deleteMission = async (id: number): Promise<boolean> => {
    try {
      const res = await fetch(`http://localhost:8000/missions/${id}`, {
        method: 'DELETE',
        headers: authHeaders(),
      })
      if (res.ok) {
        setMissions(prev => prev.filter(m => m.id !== id))
        return true
      }
      return false
    } catch {
      return false
    }
  }

  useEffect(() => {
    fetchMissions(true)
  }, [])

  useEffect(() => {
    const hasActive = missions.some(m => m.status === 'active')
    if (!hasActive) return
    const id = setInterval(fetchMissions, 10_000)
    return () => clearInterval(id)
  }, [missions])

  return { missions, loading, refetch: fetchMissions, fetchDetail, deleteMission }
}
