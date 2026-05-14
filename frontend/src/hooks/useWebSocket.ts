import { useEffect, useRef, useState } from 'react'
import type { WsMessage } from '../types'

interface UseWebSocketReturn {
  lastMessage: WsMessage | null
  isConnected: boolean
}

export function useWebSocket(url: string | null): UseWebSocketReturn {
  const [lastMessage, setLastMessage] = useState<WsMessage | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (!url) {
      setIsConnected(false)
      setLastMessage(null)
      return
    }

    function connect() {
      if (wsRef.current) {
        wsRef.current.onclose = null
        wsRef.current.close()
      }
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current)
        reconnectTimerRef.current = null
      }

      const ws = new WebSocket(url!)

      ws.onopen = () => {
        console.log('WebSocket conectado')
        setIsConnected(true)
      }

      ws.onmessage = (event: MessageEvent) => {
        const message = JSON.parse(event.data as string) as WsMessage
        setLastMessage(message)
      }

      ws.onclose = () => {
        setIsConnected(false)
        reconnectTimerRef.current = setTimeout(connect, 2000)
      }

      ws.onerror = () => ws.close()

      wsRef.current = ws
    }

    connect()

    return () => {
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

  return { lastMessage, isConnected }
}
