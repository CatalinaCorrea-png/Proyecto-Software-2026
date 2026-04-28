# AeroSearch AI

Sistema de búsqueda y rescate con dron, detección de personas en tiempo real con YOLOv8 y visualización en mapa.

---

## Requisitos previos

- [Python 3.11+](https://www.python.org/downloads/)
- [Node.js 18+](https://nodejs.org/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (para PostgreSQL)

---

## 1. Base de datos — PostgreSQL con Docker

Asegurate de tener Docker Desktop abierto y corriendo, luego ejecutá:

```bash
docker run -d \
  --name aerosearch-db \
  -e POSTGRES_USER=aerosearch \
  -e POSTGRES_PASSWORD=aerosearch \
  -e POSTGRES_DB=aerosearch \
  -p 5432:5432 \
  postgres:16
```

> **Windows (Git Bash / CMD):** si el comando con `\` falla, usá una sola línea:
> ```bash
> docker run -d --name aerosearch-db -e POSTGRES_USER=aerosearch -e POSTGRES_PASSWORD=aerosearch -e POSTGRES_DB=aerosearch -p 5432:5432 postgres:16
> ```

Para verificar que el contenedor está corriendo:

```bash
docker ps
```

Para detenerlo / reiniciarlo en el futuro:

```bash
docker stop aerosearch-db
docker start aerosearch-db
```

---

## 2. Backend — FastAPI

### 2.1 Crear el archivo `.env`

Dentro de la carpeta `backend/`, creá un archivo llamado `.env` con el siguiente contenido:

```env
DATABASE_URL=postgresql+asyncpg://aerosearch:aerosearch@localhost:5432/aerosearch
DB_ECHO=False

STORAGE_BACKEND=local
IMAGES_LOCAL_ROOT=media/detections

CAMERA_SOURCE=webcam
ESP32_STREAM_URL=http://192.168.1.1:81/stream
```

> El archivo `.env` **no se sube al repositorio** (está en `.gitignore`). Cada desarrollador crea el suyo localmente.

Valores para `CAMERA_SOURCE`:

| Valor | Descripción |
|-------|-------------|
| `webcam` | Cámara integrada del equipo (índice 0) |
| `webcam_1` | Segunda cámara (índice 1) |
| `camo` | App Camo como cámara virtual |
| `esp32` | Stream MJPEG del ESP32-CAM |
| `synthetic` | Sin cámara — genera frames de prueba |

### 2.2 Instalar dependencias

```bash
cd backend
pip install -r requirements.txt
```

### 2.3 Levantar el servidor

```bash
uvicorn main:app --reload --port 8000
```

Al arrancar por primera vez se crean automáticamente las tablas en PostgreSQL.

Verificá que esté corriendo en: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 3. Frontend — React + Vite

```bash
cd frontend
pnpm install
pnpm run dev
```

La app queda disponible en: [http://localhost:5173](http://localhost:5173)

---

## 4. Estructura del proyecto

```
Proyecto-Software-2026/
├── backend/
│   ├── main.py                  # Entry point FastAPI
│   ├── .env                     # Variables de entorno (no commitear)
│   ├── requirements.txt
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   └── state.py             # Estado global del dron y grilla
│   ├── persistence/
│   │   ├── models.py            # Modelos SQLAlchemy
│   │   ├── schemas.py           # DTOs Pydantic
│   │   ├── routers/             # Endpoints REST
│   │   ├── repositories/        # Acceso a DB
│   │   └── services/            # Lógica de negocio
│   └── modules/
│       ├── detection/           # YOLO, térmica, fusión
│       └── drone/               # Simulador, cámara
└── frontend/
    └── src/
        ├── pages/
        │   ├── Dashboard.tsx        # Vista principal en tiempo real
        │   └── DetectionsHistory.tsx # Historial de detecciones
        ├── components/
        ├── hooks/
        └── types.ts
```

---

## 5. API — endpoints principales

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/docs` | Swagger UI interactivo |
| `POST` | `/api/missions` | Crear una misión |
| `GET` | `/api/missions` | Listar misiones |
| `GET` | `/api/detections` | Listar detecciones (con filtros) |
| `GET` | `/api/detections/{id}` | Detección con imágenes |
| `GET` | `/api/images/file/{path}` | Servir imagen local |
| `WS` | `/ws/mission` | Telemetría del dron |
| `WS` | `/ws/detection` | Stream de video + detecciones IA |
| `WS` | `/ws/grid` | Grilla de cobertura |

---

## 6. Problemas comunes

**`failed to connect to the docker API`**
→ Docker Desktop no está corriendo. Abrilo desde el menú de inicio y esperá que el ícono de la ballena deje de parpadear.

**`pydantic.errors.PydanticUserError: A non-annotated attribute`**
→ Asegurate de que `CAMERA_SOURCE` esté fuera de la clase `Settings` en `core/config.py`.

**El contenedor ya existe (`Conflict`)**
→ Ya corriste el `docker run` antes. Solo hacé `docker start aerosearch-db`.

**Puerto 5432 ocupado**
→ Tenés PostgreSQL instalado localmente. Detené ese servicio o cambiá el puerto en el `docker run` a `-p 5433:5432` y actualizá el `DATABASE_URL` en `.env` a `...@localhost:5433/...`.