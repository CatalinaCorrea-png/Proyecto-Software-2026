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
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const closedOnPurposeRef = useRef(false) // ← para distinguir cierre intencional vs inesperado

  const connect = useCallback(() => {
    // Strict mode 
    // Desactiva el onclose de la conexión anterior para que no reconecte
    if (wsRef.current) {
      wsRef.current.onclose = null
      wsRef.current.close()
    }
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current)
      reconnectTimerRef.current = null
    }
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
      setIsConnected(false)
      // Solo reconecta si el cierre NO fue intencional (cleanup de React)
      if (!closedOnPurposeRef.current) {
        console.log('🔌 WebSocket desconectado, reconectando...')
        reconnectTimerRef.current = setTimeout(connect, 2000)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      ws.close()
    }

    wsRef.current = ws
  }, [url])

  useEffect(() => {
    connect() // se ejecuta una sola vez al montar el componente
    return () => {
      // Marca cierre intencional para que onclose NO reconecte
      closedOnPurposeRef.current = true
      // Cancela cualquier reconexión pendiente
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current)
        reconnectTimerRef.current = null
      }
      wsRef.current?.close()
    }
  }, [connect])

  return { lastMessage, isConnected }
}