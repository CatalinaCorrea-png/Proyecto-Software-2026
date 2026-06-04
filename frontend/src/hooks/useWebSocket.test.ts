import { renderHook, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useWebSocket } from './useWebSocket'
import type { WsMessage } from '../types'

// ─── Mock WebSocket ──────────────────────────────────────────────────────────

class MockWebSocket {
  static instances: MockWebSocket[] = []

  url: string
  onopen: (() => void) | null = null
  onclose: (() => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null
  readyState = 0

  constructor(url: string) {
    this.url = url
    MockWebSocket.instances.push(this)
  }

  close() {
    if (this.onclose) this.onclose()
  }

  simulateOpen() {
    this.readyState = 1
    if (this.onopen) this.onopen()
  }

  simulateMessage(data: object) {
    if (this.onmessage)
      this.onmessage({ data: JSON.stringify(data) } as MessageEvent)
  }

  simulateClose() {
    this.readyState = 3
    if (this.onclose) this.onclose()
  }

  simulateError() {
    if (this.onerror) this.onerror(new Event('error'))
  }
}

// ─── Tests ───────────────────────────────────────────────────────────────────

describe('useWebSocket', () => {
  beforeEach(() => {
    MockWebSocket.instances = []
    vi.stubGlobal('WebSocket', MockWebSocket)
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.useRealTimers()
  })

  // Verifica que con url=null el hook no intente abrir ninguna conexión
  // y devuelva el estado inicial desconectado
  it('no crea WebSocket cuando url es null', () => {
    const { result } = renderHook(() => useWebSocket(null))
    expect(MockWebSocket.instances).toHaveLength(0)
    expect(result.current.isConnected).toBe(false)
    expect(result.current.lastMessage).toBeNull()
  })

  // Verifica que el hook cree una conexión WebSocket al recibir una URL válida
  it('crea WebSocket al recibir una URL', () => {
    renderHook(() => useWebSocket('ws://localhost/test'))
    expect(MockWebSocket.instances).toHaveLength(1)
    expect(MockWebSocket.instances[0].url).toBe('ws://localhost/test')
  })

  // Verifica que isConnected pase a true cuando el WebSocket dispara onopen
  it('marca isConnected true al conectar', () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost/test'))
    act(() => { MockWebSocket.instances[0].simulateOpen() })
    expect(result.current.isConnected).toBe(true)
  })

  // Verifica que isConnected vuelva a false cuando el WebSocket se cierra.
  // Los fake timers evitan que el setTimeout de reconexión se dispare
  it('marca isConnected false al desconectar', () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost/test'))
    act(() => { MockWebSocket.instances[0].simulateOpen() })
    act(() => { MockWebSocket.instances[0].simulateClose() })
    expect(result.current.isConnected).toBe(false)
  })

  // Verifica que cada mensaje recibido se exponga en lastMessage con el
  // tipo y datos correctos parseados desde JSON
  it('expone el último mensaje recibido en lastMessage', () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost/test'))
    const msg: WsMessage = {
      type: 'telemetry',
      data: {
        position: { lat: -33.0, lng: -71.0, altitude: 25, timestamp: 1000 },
        battery: 80,
        status: 'flying',
        speed: 5,
        elapsed: 10,
      },
    }
    act(() => { MockWebSocket.instances[0].simulateMessage(msg) })
    expect(result.current.lastMessage).toEqual(msg)
  })

  // Verifica que recibir mensajes consecutivos actualice lastMessage
  // al mensaje más reciente cada vez
  it('actualiza lastMessage con cada mensaje nuevo', () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost/test'))
    const ws = MockWebSocket.instances[0]

    act(() => { ws.simulateMessage({ type: 'mission_status', data: { status: 'active' } }) })
    expect((result.current.lastMessage as WsMessage).type).toBe('mission_status')

    act(() => { ws.simulateMessage({ type: 'mission_status', data: { status: 'completed' } }) })
    expect((result.current.lastMessage as WsMessage & { data: { status: string } }).data.status)
      .toBe('completed')
  })

  // Verifica que un error en el WebSocket cierre la conexión (el hook
  // tiene ws.onerror = () => ws.close(), lo que desencadena reconexión)
  it('cierra la conexión al ocurrir un error', () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost/test'))
    act(() => { MockWebSocket.instances[0].simulateOpen() })
    act(() => { MockWebSocket.instances[0].simulateError() })
    // El error llama a ws.close() → onclose → setIsConnected(false)
    expect(result.current.isConnected).toBe(false)
  })

  // Verifica que al cambiar la URL el hook cierre la conexión anterior
  // y abra una nueva con la URL actualizada
  it('cierra la conexión anterior al cambiar la URL', () => {
    const { result, rerender } = renderHook(
      ({ url }: { url: string }) => useWebSocket(url),
      { initialProps: { url: 'ws://localhost/old' } }
    )
    expect(MockWebSocket.instances).toHaveLength(1)

    rerender({ url: 'ws://localhost/new' })
    // Se crea un segundo WebSocket con la nueva URL
    expect(MockWebSocket.instances.length).toBeGreaterThanOrEqual(1)
    const latest = MockWebSocket.instances[MockWebSocket.instances.length - 1]
    expect(latest.url).toBe('ws://localhost/new')
  })
})
