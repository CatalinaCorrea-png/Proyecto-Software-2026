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
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  // Mapa para actualizaciones rápidas sin recorrer el array
  const cellMapRef = useRef<Map<string, GridCell>>(new Map())

  useEffect(() => {
    let cancelled = false

    function connect() {
      if (cancelled) return

      if (wsRef.current) {
        wsRef.current.onclose = null
        wsRef.current.close()
      }
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current)
        reconnectTimerRef.current = null
      }

      const ws = new WebSocket(url)

      ws.onopen = () => { if (!cancelled) setIsConnected(true) }
      ws.onclose = () => {
        if (cancelled) return
        setIsConnected(false)
        reconnectTimerRef.current = setTimeout(connect, 2000)
      }

      ws.onmessage = (event) => {
        if (cancelled) return
        const msg = JSON.parse(event.data as string) as
          | { type: 'grid_init'; cells: GridCell[]; coverage: number }
          | { type: 'grid_update'; cells: GridCell[]; coverage: number }

        if (msg.type === 'grid_init') {
          const map = new Map<string, GridCell>()
          msg.cells.forEach(c => map.set(`${c.row}-${c.col}`, c))
          cellMapRef.current = map
          setCells(msg.cells)
          setCoverage(msg.coverage)
        }

        if (msg.type === 'grid_update') {
          msg.cells.forEach(c => {
            cellMapRef.current.set(`${c.row}-${c.col}`, c)
          })
          setCells(Array.from(cellMapRef.current.values()))
          setCoverage(msg.coverage)
        }
      }

      wsRef.current = ws
    }

    // El setTimeout(0) deja que el ciclo de StrictMode (mount→unmount) termine
    // antes de crear el socket, evitando el warning "closed before established".
    connect()

    return () => {
      cancelled = true
      if (wsRef.current) {
        wsRef.current.onclose = null
        wsRef.current.close()
      }
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current)
        reconnectTimerRef.current = null
      }
    }
  }, [url])

  return { cells, coverage, isConnected }
}