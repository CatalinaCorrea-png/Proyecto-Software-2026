import { renderHook, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useDetectionFeed } from './useDetectionFeed'
import type { Detection } from '../types'

// ─── Mock WebSocket ──────────────────────────────────────────────────────────

class MockWebSocket {
  static instances: MockWebSocket[] = []

  url: string
  onopen: (() => void) | null = null
  onclose: (() => void) | null = null
  onmessage: ((event: { data: string }) => void) | null = null
  onerror: (() => void) | null = null
  readyState = 0

  constructor(url: string) {
    this.url = url
    MockWebSocket.instances.push(this)
  }

  close() {
    if (this.onclose) this.onclose()
  }

  // Helpers para simular eventos del servidor
  simulateOpen() {
    this.readyState = 1
    if (this.onopen) this.onopen()
  }

  simulateMessage(data: object) {
    if (this.onmessage) this.onmessage({ data: JSON.stringify(data) })
  }

  simulateClose() {
    this.readyState = 3
    if (this.onclose) this.onclose()
  }
}

const makeDetection = (id: string, overrides: Partial<Detection> = {}): Detection => ({
  id,
  position: { lat: -33.0, lng: -71.0, altitude: 25, timestamp: Number(id) },
  confidence: 'medium',
  source: 'rgb',
  timestamp: Number(id),
  ...overrides,
})

// ─── Tests ───────────────────────────────────────────────────────────────────

describe('useDetectionFeed', () => {
  beforeEach(() => {
    MockWebSocket.instances = []
    vi.stubGlobal('WebSocket', MockWebSocket)
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.useRealTimers()
  })

  // Verifica que el hook empiece en estado desconectado, sin frame
  // cargado y con la lista de detecciones vacía antes de establecer conexión
  it('inicia desconectado sin datos', () => {
    const { result } = renderHook(() => useDetectionFeed('ws://localhost/test'))
    expect(result.current.isConnected).toBe(false)
    expect(result.current.framePayload).toBeNull()
    expect(result.current.detections).toEqual([])
  })

  // Verifica que isConnected pase a true cuando el WebSocket
  // dispara el evento onopen (conexión establecida con el backend)
  it('marca isConnected true al abrir conexión', () => {
    const { result } = renderHook(() => useDetectionFeed('ws://localhost/test'))
    act(() => { MockWebSocket.instances[0].simulateOpen() })
    expect(result.current.isConnected).toBe(true)
  })

  // Verifica que isConnected vuelva a false cuando el WebSocket cierra.
  // Los fake timers evitan que el setTimeout de reconexión se dispare automáticamente
  it('marca isConnected false al cerrar conexión', () => {
    const { result } = renderHook(() => useDetectionFeed('ws://localhost/test'))
    act(() => { MockWebSocket.instances[0].simulateOpen() })
    expect(result.current.isConnected).toBe(true)
    // Con fake timers activos el setTimeout de reconexión no se dispara
    act(() => { MockWebSocket.instances[0].simulateClose() })
    expect(result.current.isConnected).toBe(false)
  })

  // Verifica que al recibir un mensaje tipo "frame" el hook actualice
  // framePayload con el frame RGB, overlay térmico y detecciones fusionadas
  it('actualiza framePayload con mensajes de tipo frame', () => {
    const { result } = renderHook(() => useDetectionFeed('ws://localhost/test'))
    const frameMsg = {
      type: 'frame',
      frame: 'base64data==',
      thermal_overlay: 'thermaldata==',
      fused_detections: [{ confidence: 'high', source: 'fusion', temperature: 36.5 }],
      detection_count: 1,
    }
    act(() => { MockWebSocket.instances[0].simulateMessage(frameMsg) })
    expect(result.current.framePayload).toEqual(frameMsg)
  })

  // Verifica que un mensaje "detection_history" reemplace completamente
  // la lista de detecciones (carga inicial al conectar con el backend)
  it('reemplaza detections completas con detection_history', () => {
    const history = [makeDetection('1'), makeDetection('2')]
    const { result } = renderHook(() => useDetectionFeed('ws://localhost/test'))
    act(() => {
      MockWebSocket.instances[0].simulateMessage({ type: 'detection_history', data: history })
    })
    expect(result.current.detections).toEqual(history)
  })

  // Verifica que una nueva detección individual se anteponga al inicio de la lista
  // (más reciente primero) en lugar de agregarse al final
  it('antepone nueva detección individual al inicio de la lista', () => {
    const { result } = renderHook(() => useDetectionFeed('ws://localhost/test'))
    act(() => {
      MockWebSocket.instances[0].simulateMessage({
        type: 'detection_history',
        data: [makeDetection('1'), makeDetection('2')],
      })
    })
    const newDet = makeDetection('99', { confidence: 'high', source: 'fusion' })
    act(() => {
      MockWebSocket.instances[0].simulateMessage({ type: 'detection', data: newDet })
    })
    expect(result.current.detections[0]).toEqual(newDet)
    expect(result.current.detections).toHaveLength(3)
  })

  // Verifica que la lista de detecciones no supere los 100 elementos,
  // descartando las más antiguas al agregar una nueva cuando ya está llena
  it('limita la lista de detecciones a 100 elementos', () => {
    const { result } = renderHook(() => useDetectionFeed('ws://localhost/test'))
    const initial = Array.from({ length: 100 }, (_, i) => makeDetection(String(i)))
    act(() => {
      MockWebSocket.instances[0].simulateMessage({ type: 'detection_history', data: initial })
    })
    expect(result.current.detections).toHaveLength(100)

    // Agregar uno más → debe seguir en 100
    act(() => {
      MockWebSocket.instances[0].simulateMessage({
        type: 'detection',
        data: makeDetection('999', { confidence: 'high' }),
      })
    })
    expect(result.current.detections).toHaveLength(100)
    expect(result.current.detections[0].id).toBe('999')
  })

  // Verifica que mensajes con tipo desconocido sean ignorados silenciosamente
  // sin modificar framePayload ni la lista de detecciones
  it('ignora mensajes con tipo desconocido', () => {
    const { result } = renderHook(() => useDetectionFeed('ws://localhost/test'))
    act(() => {
      MockWebSocket.instances[0].simulateMessage({ type: 'unknown', data: {} })
    })
    expect(result.current.framePayload).toBeNull()
    expect(result.current.detections).toEqual([])
  })
})
