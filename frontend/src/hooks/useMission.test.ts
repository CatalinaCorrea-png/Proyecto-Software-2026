import { renderHook } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { useMission } from './useMission'
import type { WsMessage } from '../types'

const makeTelemetryMsg = (lat: number, lng: number, i = 0): WsMessage => ({
  type: 'telemetry',
  data: {
    position: { lat, lng, altitude: 25.0, timestamp: i },
    battery: 80,
    status: 'flying',
    speed: 5,
    elapsed: i,
  },
})

describe('useMission', () => {
  // Verifica que el hook inicie con telemetría en null y trail vacío
  // cuando todavía no llegó ningún mensaje del WebSocket
  it('empieza con telemetría null y trail vacío', () => {
    const { result } = renderHook(() => useMission(null))
    expect(result.current.telemetry).toBeNull()
    expect(result.current.trail).toEqual([])
  })

  // Verifica que el hook ignore mensajes de otros tipos (ej. mission_status)
  // y no modifique el estado de telemetría ni el trail
  it('ignora mensajes que no son telemetría', () => {
    const msg: WsMessage = { type: 'mission_status', data: { status: 'active' } }
    const { result } = renderHook(() => useMission(msg))
    expect(result.current.telemetry).toBeNull()
    expect(result.current.trail).toEqual([])
  })

  // Verifica que al recibir un mensaje tipo "telemetry" el estado
  // de telemetría se actualice con los datos del mensaje
  it('actualiza telemetría al recibir mensaje tipo telemetry', () => {
    const msg = makeTelemetryMsg(-33.0, -71.0)
    const { result } = renderHook(() => useMission(msg))
    expect(result.current.telemetry).toEqual(msg.data)
  })

  // Verifica que cada mensaje de telemetría agregue un punto {lat, lng}
  // al trail con las coordenadas GPS correctas
  it('agrega punto al trail con cada mensaje de telemetría', () => {
    const msg = makeTelemetryMsg(-33.0, -71.0)
    const { result } = renderHook(() => useMission(msg))
    expect(result.current.trail).toHaveLength(1)
    expect(result.current.trail[0]).toEqual({ lat: -33.0, lng: -71.0 })
  })

  // Verifica que el trail acumule todos los puntos recibidos en orden,
  // reflejando la ruta real del drone mensaje a mensaje
  it('acumula puntos en el trail con cada mensaje nuevo', () => {
    const { result, rerender } = renderHook(
      ({ msg }: { msg: WsMessage }) => useMission(msg),
      { initialProps: { msg: makeTelemetryMsg(-33.0, -71.0, 0) } }
    )
    expect(result.current.trail).toHaveLength(1)

    rerender({ msg: makeTelemetryMsg(-33.1, -71.1, 1) })
    expect(result.current.trail).toHaveLength(2)

    rerender({ msg: makeTelemetryMsg(-33.2, -71.2, 2) })
    expect(result.current.trail).toHaveLength(3)
    expect(result.current.trail[2]).toEqual({ lat: -33.2, lng: -71.2 })
  })

  // Verifica que el trail no supere los 200 puntos para evitar consumo
  // excesivo de memoria en misiones largas, descartando los puntos más antiguos
  it('limita el trail a 200 puntos', () => {
    const { result, rerender } = renderHook(
      ({ msg }: { msg: WsMessage }) => useMission(msg),
      { initialProps: { msg: makeTelemetryMsg(-33.0, -71.0, 0) } }
    )

    // Agregar 200 mensajes más (total 201)
    for (let i = 1; i <= 200; i++) {
      rerender({ msg: makeTelemetryMsg(-33.0 + i * 0.001, -71.0, i) })
    }

    expect(result.current.trail).toHaveLength(200)
    // El último punto debe ser el más reciente
    expect(result.current.trail[199].lat).toBeCloseTo(-33.0 + 200 * 0.001, 5)
  })

  // Verifica que al pasar null como mensaje (sin misión activa)
  // el hook limpie la telemetría y el trail completamente
  it('resetea estado cuando se pasa null', () => {
    const { result, rerender } = renderHook(
      ({ msg }: { msg: WsMessage | null }) => useMission(msg),
      { initialProps: { msg: makeTelemetryMsg(-33.0, -71.0) as WsMessage | null } }
    )
    expect(result.current.trail).toHaveLength(1)

    rerender({ msg: null })
    expect(result.current.telemetry).toBeNull()
    expect(result.current.trail).toEqual([])
  })
})
