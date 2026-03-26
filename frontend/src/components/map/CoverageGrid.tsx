import { Rectangle, Tooltip } from 'react-leaflet'
import type { GridCell } from '../../hooks/useSearchGrid'

interface Props {
  cells: GridCell[]
}

// Tamaño de celda en grados (debe coincidir con el backend)
const CELL_LAT = 20 / 111_000
const CELL_LNG = 20 / (111_000 * Math.cos((- 34.6 * Math.PI) / 180))

export function CoverageGrid({ cells }: Props) {
  return (
    <>
      {cells.map(cell => {
        // Solo dibujar celdas relevantes para no saturar el mapa
        if (cell.status === 'unexplored') {
          // Borde muy sutil para ver el área total
          return (
            <Rectangle
              key={`${cell.row}-${cell.col}`}
              bounds={[
                [cell.lat, cell.lng],
                [cell.lat - CELL_LAT, cell.lng + CELL_LNG]
              ]}
              pathOptions={{
                color: '#1E3A5F',
                weight: 0.5,
                fillOpacity: 0,
                opacity: 0.4
              }}
            />
          )
        }

        if (cell.status === 'explored') {
          return (
            <Rectangle
              key={`${cell.row}-${cell.col}`}
              bounds={[
                [cell.lat, cell.lng],
                [cell.lat - CELL_LAT, cell.lng + CELL_LNG]
              ]}
              pathOptions={{
                color: '#00BCD4',
                weight: 0.5,
                fillColor: '#00BCD4',
                fillOpacity: 0.15,
                opacity: 0.6
              }}
            >
              <Tooltip sticky>
                Explorada {cell.explored_at
                  ? new Date(cell.explored_at).toLocaleTimeString()
                  : ''}
              </Tooltip>
            </Rectangle>
          )
        }

        if (cell.status === 'detection') {
          return (
            <Rectangle
              key={`${cell.row}-${cell.col}`}
              bounds={[
                [cell.lat, cell.lng],
                [cell.lat - CELL_LAT, cell.lng + CELL_LNG]
              ]}
              pathOptions={{
                color: '#FF6D00',
                weight: 1.5,
                fillColor: '#FF6D00',
                fillOpacity: 0.3,
                opacity: 1
              }}
            >
              <Tooltip sticky>⚠️ Detección registrada</Tooltip>
            </Rectangle>
          )
        }

        return null
      })}
    </>
  )
}