import { useEffect, useState, useCallback } from 'react'

export interface DetectionRecord {
  id: string
  latitude: number
  longitude: number
  altitude: number | null
  confidence: 'low' | 'medium' | 'high'
  source: string
  temperature: number | null
  raw_confidence_score: number | null
  detected_at: string
  images: {
    id: string
    image_type: string
    url: string
  }[]
}

export function useDetections() {
  const [detections, setDetections] = useState<DetectionRecord[]>([])
  const [loading, setLoading] = useState(true)

  const fetchDetections = useCallback(async () => {
    setLoading(true)
    const res = await fetch('http://localhost:8000/api/detections?limit=100')
    const data = await res.json()
    setDetections(data)
    setLoading(false)
  }, [])

  useEffect(() => {
    fetchDetections()
  }, [fetchDetections])

  return { detections, loading, refetch: fetchDetections }
}