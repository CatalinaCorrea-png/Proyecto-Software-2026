import { useEffect, useRef, useState } from 'react'
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
  const urlRef = useRef(url)
  urlRef.current = url

  useEffect(() => {
    function connect() {
      // Limpia conexión anterior (StrictMode monta → desmonta → monta)
      if (wsRef.current) {
        wsRef.current.onclose = null
        wsRef.current.close()
      }
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current)
        reconnectTimerRef.current = null
      }

      const ws = new WebSocket(urlRef.current) // abre conexión al backend

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
        console.log('🔌 WebSocket desconectado, reconectando...')
        reconnectTimerRef.current = setTimeout(connect, 2000) // reconexión automática
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        ws.close()
      }

      wsRef.current = ws
    }

    connect()

    return () => {
      // Desactiva onclose para que no reconecte al desmontar
      if (wsRef.current) {
        wsRef.current.onclose = null
        wsRef.current.close()
      }
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current)
        reconnectTimerRef.current = null
      }
    }
  }, []) // ← se ejecuta una sola vez al montar

  return { lastMessage, isConnected }
}