import { renderHook, waitFor, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useMissions } from './useMissions'
import type { Mission } from './useMissions'

const mockMission: Mission = {
  id: 1,
  name: 'Misión de prueba',
  status: 'completed',
  created_at: '2026-06-01T10:00:00Z',
  started_at: null,
  ended_at: null,
  initial_battery: 100,
  final_battery: 85,
  coverage_percent: 72.5,
  detections_count: 3,
  altitude: 25,
  cell_size_m: 20,
  grid_rows: 10,
  grid_cols: 10,
  grid_center_lat: -33.0,
  grid_center_lng: -71.0,
}

// ─── Tests ───────────────────────────────────────────────────────────────────

describe('useMissions', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  // Verifica que el hook empiece con loading=true y missions vacío
  // mientras el fetch inicial todavía no retornó respuesta
  it('inicia con loading=true y missions vacío antes de la primera respuesta', () => {
    vi.stubGlobal('fetch', vi.fn().mockImplementation(() => new Promise(() => {})))
    const { result } = renderHook(() => useMissions())
    expect(result.current.loading).toBe(true)
    expect(result.current.missions).toEqual([])
  })

  // Verifica que tras una respuesta exitosa loading pase a false
  // y missions se poblen con los datos retornados por la API
  it('carga las misiones y pone loading=false tras respuesta exitosa', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      json: async () => [mockMission],
    }))
    const { result } = renderHook(() => useMissions())
    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.missions).toHaveLength(1)
    expect(result.current.missions[0].id).toBe(1)
  })

  // Verifica que si la API falla (error de red) missions quede vacío
  // y loading pase a false de todas formas (el finally del hook lo garantiza)
  it('pone loading=false y mantiene missions vacío si el fetch falla', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('Network error')))
    const { result } = renderHook(() => useMissions())
    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.missions).toEqual([])
  })

  // Verifica que deleteMission elimine la misión del estado local
  // cuando el servidor responde con ok=true
  it('deleteMission elimina la misión del estado local si el servidor responde ok', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ json: async () => [mockMission] }) // carga inicial
      .mockResolvedValueOnce({ ok: true })                         // DELETE

    vi.stubGlobal('fetch', fetchMock)
    const { result } = renderHook(() => useMissions())
    await waitFor(() => expect(result.current.missions).toHaveLength(1))

    let success = false
    await act(async () => {
      success = await result.current.deleteMission(1)
    })

    expect(success).toBe(true)
    expect(result.current.missions).toHaveLength(0)
  })

  // Verifica que deleteMission retorne false y no modifique el estado
  // cuando el servidor responde con ok=false (ej. 409 o 403)
  it('deleteMission retorna false si el servidor responde con error', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ json: async () => [mockMission] })
      .mockResolvedValueOnce({ ok: false })

    vi.stubGlobal('fetch', fetchMock)
    const { result } = renderHook(() => useMissions())
    await waitFor(() => expect(result.current.missions).toHaveLength(1))

    let success = true
    await act(async () => {
      success = await result.current.deleteMission(1)
    })

    expect(success).toBe(false)
    expect(result.current.missions).toHaveLength(1) // no se eliminó
  })

  // Verifica que refetch actualice la lista de misiones sin activar
  // el spinner de carga (showSpinner=false por defecto)
  it('refetch actualiza missions sin cambiar loading', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ json: async () => [] })
      .mockResolvedValueOnce({ json: async () => [mockMission] })

    vi.stubGlobal('fetch', fetchMock)
    const { result } = renderHook(() => useMissions())
    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.missions).toHaveLength(0)

    await act(async () => { await result.current.refetch() })

    expect(result.current.missions).toHaveLength(1)
    expect(result.current.loading).toBe(false)
  })
})
