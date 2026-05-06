import { useState, useCallback } from 'react'
import axios from 'axios'
import type { ImageMeta, ImageListResponse } from '../types'

const API = 'http://localhost:8000'

interface GalleryFilters {
  mission_id?: string
  has_detections?: boolean
  page?: number
  page_size?: number
}

export function useImageGallery() {
  const [images, setImages] = useState<ImageMeta[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchImages = useCallback(async (filters: GalleryFilters = {}) => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams()
      if (filters.mission_id) params.set('mission_id', filters.mission_id)
      if (filters.has_detections !== undefined)
        params.set('has_detections', String(filters.has_detections))
      params.set('page', String(filters.page ?? 1))
      params.set('page_size', String(filters.page_size ?? 20))

      const { data } = await axios.get<ImageListResponse>(`${API}/api/images?${params}`)
      setImages(data.items)
      setTotal(data.total)
    } catch {
      setError('Error cargando imágenes')
    } finally {
      setLoading(false)
    }
  }, [])

  const getFullImageUrl = (imageId: string) => `${API}/api/images/${imageId}/full`

  return { images, total, loading, error, fetchImages, getFullImageUrl }
}
