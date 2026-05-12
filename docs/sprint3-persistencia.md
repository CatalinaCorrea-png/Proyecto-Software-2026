# Sprint 3 — Persistencia de Misiones en Base de Datos

## Descripción general

Se implementó una capa de persistencia completa para el sistema AeroSearch AI.
Toda la información de las misiones de búsqueda (trayectoria, detecciones de personas,
cobertura de grilla) ahora queda guardada en una base de datos SQLite local, y se
puede consultar desde el frontend a través de una nueva sección de historial.

---

## Tecnologías utilizadas

| Componente | Tecnología |
|------------|------------|
| Base de datos | SQLite (archivo `backend/aerosearch.db`) |
| ORM | SQLAlchemy 2.x (Mapped / DeclarativeBase) |
| Geocodificación inversa | Nominatim API (OpenStreetMap) |
| Frontend | React + TypeScript (hook personalizado) |

---

## Diagrama MER

Ver archivo [`MER.svg`](./MER.svg) en esta misma carpeta.

### Relaciones

```
MISSIONS (1) ──────────── (N) DETECTIONS
MISSIONS (1) ──────────── (N) GRID_CELLS
```

---

## Estructura de archivos agregados

```
backend/
├── db/
│   ├── __init__.py
│   ├── database.py        ← engine SQLite, SessionLocal, Base, init_db()
│   └── models.py          ← modelos ORM: Mission, Detection, GridCell
└── aerosearch.db          ← base de datos local (excluida del repo)

frontend/src/
├── hooks/
│   └── useMissions.ts     ← hook para fetch de misiones y detalle
└── pages/
    └── MissionsHistory.tsx ← página de historial con cards y modal
```

---
## Documentacion  Swagger OpenAPI

Acá se puede encontrar documentados los endpoints de persistencia de las misiones y ademas consumirlos para ver la informacion almacenada en las tablas http://localhost:8000/docs#/

## Tablas

### `missions`

Registra cada sesión de búsqueda con su metadata completa.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | INTEGER PK | Identificador autoincremental |
| `created_at` | DATETIME | Momento de creación del registro |
| `started_at` | DATETIME | Inicio del vuelo (nullable) |
| `ended_at` | DATETIME | Fin del vuelo (nullable) |
| `status` | VARCHAR | `active` · `completed` · `aborted` |
| `initial_battery` | FLOAT | Batería al inicio (100.0) |
| `final_battery` | FLOAT | Batería al terminar (nullable) |
| `coverage_percent` | FLOAT | % de grilla explorada al finalizar |
| `detections_count` | INTEGER | Total de detecciones registradas |
| `grid_rows` | INTEGER | Filas de la grilla de búsqueda |
| `grid_cols` | INTEGER | Columnas de la grilla de búsqueda |
| `grid_center_lat` | FLOAT | Latitud del centro de la zona |
| `grid_center_lng` | FLOAT | Longitud del centro de la zona |

### `detections`

Cada detección de persona registrada durante una misión.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | VARCHAR PK | UUID de la detección |
| `mission_id` | INTEGER FK | Misión a la que pertenece |
| `timestamp` | DATETIME | Momento exacto de la detección |
| `position_lat` | FLOAT | Latitud GPS del dron al detectar |
| `position_lng` | FLOAT | Longitud GPS del dron al detectar |
| `position_altitude` | FLOAT | Altitud del dron (metros) |
| `confidence` | VARCHAR | `high` (RGB + Térmica) · `medium` (una fuente) |
| `source` | VARCHAR | `fusion` · `rgb` · `thermal` |
| `temperature` | FLOAT | Temperatura corporal estimada (°C, nullable) |
| `rgb_confidence` | FLOAT | Score del modelo YOLO (0.0–1.0, nullable) |

### `grid_cells`

Snapshot del estado de cada celda de la grilla al finalizar la misión.
Solo se guardan celdas con `status != "unexplored"`.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | INTEGER PK | Identificador autoincremental |
| `mission_id` | INTEGER FK | Misión a la que pertenece |
| `row` | INTEGER | Fila en la grilla (0-indexed) |
| `col` | INTEGER | Columna en la grilla (0-indexed) |
| `cell_lat` | FLOAT | Latitud del centro de la celda |
| `cell_lng` | FLOAT | Longitud del centro de la celda |
| `status` | VARCHAR | `explored` · `detection` |
| `explored_at` | DATETIME | Momento en que el dron pasó por la celda |

---

## Flujo de persistencia

```
WebSocket /ws/mission  ──► conecta
       │
       ▼
  Crea registro Mission (status="active")
       │
       ▼
  Dron vuela y detecta personas
       │          │
       ▼          ▼
  Detection guardada   Grid cell actualizada
  por WebSocket        en memoria
  /ws/detection
       │
       ▼
  WebSocket /ws/mission  ──► desconecta
       │
       ▼
  Actualiza Mission:
    ended_at, status="completed",
    final_battery, coverage_percent,
    detections_count
    + snapshot de GRID_CELLS
```

**Misiones huérfanas:** al reiniciar el backend, cualquier misión que quedó
en `status="active"` de una sesión anterior se marca automáticamente como `"aborted"`.

---

## API REST

### `GET /missions`

Devuelve la lista de todas las misiones, ordenadas por fecha descendente.

```json
[
  {
    "id": 4,
    "created_at": "2026-05-03T18:00:00",
    "started_at": "2026-05-03T18:00:01",
    "ended_at": "2026-05-03T18:22:14",
    "status": "completed",
    "initial_battery": 100.0,
    "final_battery": 33.6,
    "coverage_percent": 68.2,
    "detections_count": 44,
    "grid_rows": 22,
    "grid_cols": 20,
    "grid_center_lat": -32.6532,
    "grid_center_lng": -70.0109
  }
]
```

### `GET /missions/{id}`

Devuelve el detalle completo de una misión, incluyendo todas sus detecciones.

```json
{
  "id": 4,
  "status": "completed",
  "detections": [
    {
      "id": "a1b2c3d4-...",
      "timestamp": "2026-05-03T18:05:32",
      "position_lat": -32.6554,
      "position_lng": -70.0087,
      "position_altitude": 25.0,
      "confidence": "high",
      "source": "fusion",
      "temperature": 36.7,
      "rgb_confidence": 0.91
    }
  ]
}
```

---

## Frontend — Historial de Misiones

Se agregó una nueva sección accesible desde la barra de navegación superior.

### Funcionalidades

- **Cards por misión** con zona geográfica obtenida via reverse geocoding (Nominatim/OSM),
  barra de cobertura, duración, batería consumida y conteo de detecciones.
- **Badge de estado** diferenciado: En curso (verde) · Completada (gris) · Interrumpida (rojo).
- **Modal de detalle** al hacer click en una card: tabla completa de detecciones con
  coordenadas GPS, nivel de confianza, fuente del sensor y temperatura.
- **Refresco automático** cada 10 segundos mientras haya una misión activa.
- **Navegación sin interrupciones:** el Dashboard permanece montado al cambiar de tab,
  manteniendo los WebSockets activos y la misión en curso sin afectarse.

---

## Cómo ejecutar

### Backend

```powershell
# Desde la carpeta raíz del proyecto
& ".\venv\Scripts\Activate.ps1"
cd backend
python -m uvicorn main:app --reload --port 8000
```

La base de datos `aerosearch.db` se crea automáticamente al primer arranque.

### Frontend

```powershell
cd frontend
pnpm run dev
```

Abrir `http://localhost:5173` en el navegador.

---

## Notas técnicas

- La DB usa SQLite para desarrollo local. Para producción se puede cambiar
  `DATABASE_URL` en `backend/db/database.py` a PostgreSQL sin modificar los modelos.
- El archivo `aerosearch.db` está excluido del repositorio (`.gitignore`).
- Las detecciones se guardan en tiempo real durante la misión; el snapshot de
  `grid_cells` y el cierre de la misión ocurren al desconectar el WebSocket.
