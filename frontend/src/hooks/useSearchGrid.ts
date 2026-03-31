import { useEffect, useRef, useState } from 'react'

export interface GridCell {
  row: number
  col: number
  lat: number
  lng: number
  status: 'unexplored' | 'explored' | 'detection'
  explored_at: number | null
}

interface UseSearchGridReturn {
  cells: GridCell[]
  coverage: number
  isConnected: boolean
}

export function useSearchGrid(url: string): UseSearchGridReturn {
  const [cells, setCells] = useState<GridCell[]>([])
  const [coverage, setCoverage] = useState(0)
  const [isConnected, setIsConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  // Mapa para actualizaciones rápidas sin recorrer el array
  const cellMapRef = useRef<Map<string, GridCell>>(new Map())

  useEffect(() => {
    const connect = () => {
      const ws = new WebSocket(url)

      ws.onopen = () => setIsConnected(true)
      ws.onclose = () => {
        setIsConnected(false)
        setTimeout(connect, 2000)
      }

      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data as string) as
          | { type: 'grid_init'; cells: GridCell[]; coverage: number }
          | { type: 'grid_update'; cells: GridCell[]; coverage: number }

        if (msg.type === 'grid_init') {
          // Cargar todas las celdas de una vez
          const map = new Map<string, GridCell>()
          msg.cells.forEach(c => map.set(`${c.row}-${c.col}`, c))
          cellMapRef.current = map  // construye el índice desde cero
          setCells(msg.cells)       // carga todas las celdas al estado
          setCoverage(msg.coverage)
        }

        if (msg.type === 'grid_update') {
          // Actualizar las celdas
          msg.cells.forEach(c => {
            cellMapRef.current.set(`${c.row}-${c.col}`, c) // actualiza solo las que cambiaron
          })
          setCells(Array.from(cellMapRef.current.values())) // reconstruye el array desde el Map
          setCoverage(msg.coverage)
        }
      }

      wsRef.current = ws
    }

    connect()
    return () => wsRef.current?.close()
  }, [url])

  return { cells, coverage, isConnected }
}