import { useEffect, useRef, useState, useCallback } from 'react'
import type { WsMessage } from '../types'

interface UseWebSocketReturn {
  lastMessage: WsMessage | null
  isConnected: boolean
}

export function useWebSocket(url: string): UseWebSocketReturn {
  const [lastMessage, setLastMessage] = useState<WsMessage | null>(null)
  // lastMessage = el último mensaje recibido
  // setLastMessage = la función para actualizarlo

  const [isConnected, setIsConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  const connect = useCallback(() => {
    const ws = new WebSocket(url) // abre conexión al backend

    ws.onopen = () => {
      console.log('✅ WebSocket conectado')
      setIsConnected(true)
    }

    ws.onmessage = (event: MessageEvent) => {
      const message = JSON.parse(event.data as string) as WsMessage
      setLastMessage(message) // ← cada mensaje nuevo actualiza el estado
    }

    ws.onclose = () => {
      console.log('🔌 WebSocket desconectado, reconectando...')
      setIsConnected(false)
      setTimeout(connect, 2000) // reconexión automática si se cae
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      ws.close()
    }

    wsRef.current = ws
  }, [url])

  useEffect(() => {
    connect() // se ejecuta una sola vez al montar el componente
    return () => wsRef.current?.close() // limpia cuando se desmonta
  }, [connect])

  return { lastMessage, isConnected }
}