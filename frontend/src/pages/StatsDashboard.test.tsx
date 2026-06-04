import { render, screen, waitFor, cleanup } from '@testing-library/react'
import { describe, it, expect, vi, afterEach } from 'vitest'
import { StatsDashboard } from './StatsDashboard'

const emptyData = {
  ttfd_per_mission:       [],
  sweep_efficiency:       [],
  detection_density:      [],
  battery_per_km2:        [],
  source_per_mission:     [],
  altitude_vs_confidence: [],
}

const sampleData = {
  ttfd_per_mission:       [{ label: 'M-001', ttfd_min: 3.5 }],
  sweep_efficiency:       [{ label: 'M-001', m2_per_min: 1200 }],
  detection_density:      [{ label: 'M-001', detections_per_km2: 4.2 }],
  battery_per_km2:        [{ label: 'M-001', battery_per_km2: 5.1 }],
  source_per_mission:     [{ label: 'M-001', rgb: 2, thermal: 1, fusion: 3 }],
  altitude_vs_confidence: [{ position_altitude: 25, rgb_confidence: 0.87, source: 'fusion' }],
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

// Verifica que mientras el fetch no retorna el componente muestre
// el mensaje de carga en lugar de los gráficos
it('muestra el spinner de carga mientras se obtienen los datos', () => {
  vi.stubGlobal('fetch', vi.fn().mockImplementation(() => new Promise(() => {})))
  render(<StatsDashboard />)
  screen.getByText('Cargando estadísticas...')
})

// Verifica que si el endpoint devuelve un HTTP error el componente
// muestre el mensaje de error con el código correspondiente
it('muestra mensaje de error cuando el fetch falla', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok: false,
    status: 500,
  }))
  render(<StatsDashboard />)
  await waitFor(() => screen.getByText(/Error:/))
})

// Verifica que el componente renderice sin romper cuando la API devuelve
// todos los arrays vacíos (primera vez que se usa, sin misiones registradas)
it('renderiza el título con datos vacíos sin lanzar errores', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok: true,
    json: async () => emptyData,
  }))
  render(<StatsDashboard />)
  await waitFor(() => screen.getByText('Estadísticas Operacionales'))
})

// Verifica que con arrays vacíos aparezcan los placeholders de "sin datos"
// en lugar de gráficos vacíos
it('muestra EmptyState cuando no hay misiones con detecciones', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok: true,
    json: async () => emptyData,
  }))
  render(<StatsDashboard />)
  await waitFor(() =>
    screen.getByText('Sin misiones con detecciones registradas')
  )
})

// Verifica que con datos reales el componente muestre el título de la sección
// y la barra lateral de filtros con la misión correspondiente
it('muestra el título y la sidebar con datos reales', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok: true,
    json: async () => sampleData,
  }))
  render(<StatsDashboard />)
  await waitFor(() => screen.getByText('Estadísticas Operacionales'))
  // La sidebar se muestra cuando hay misiones
  screen.getByText('FILTROS')
  // La etiqueta de la misión aparece en la sidebar
  screen.getByText('M-001')
})
