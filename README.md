<div align="center">

# AeroSearch AI

**Sistema de gestión de drones para búsqueda y rescate con visión por computadora, detección térmica y dashboard de estadísticas en tiempo real.**

<br/>

![Python](https://img.shields.io/badge/Python_3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![React](https://img.shields.io/badge/React_19-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![Vite](https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

</div>

---

## Tabla de contenidos

- [Tecnologías](#tecnologías)
- [Requisitos previos](#-requisitos-previos)
- [Instalación](#-instalación)
- [Variables de entorno](#-variables-de-entorno)
- [Credenciales de acceso](#-credenciales-de-acceso)
- [Levantar la aplicación](#-levantar-la-aplicación)
- [Levantar con Docker](#-levantar-con-docker)
- [Tests](#-tests)
- [Estructura del proyecto](#-estructura-del-proyecto)
- [Equipo](#-equipo)

---

## Tecnologías

### Backend
![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=flat-square&logo=mongodb&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=flat-square&logo=opencv&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-013243?style=flat-square&logo=numpy&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=flat-square&logo=pandas&logoColor=white)

### Frontend
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=flat-square&logo=react&logoColor=61DAFB)
![Vite](https://img.shields.io/badge/Vite-646CFF?style=flat-square&logo=vite&logoColor=white)
![Recharts](https://img.shields.io/badge/Recharts-22B5BF?style=flat-square&logo=chartdotjs&logoColor=white)
![Leaflet](https://img.shields.io/badge/Leaflet-199900?style=flat-square&logo=leaflet&logoColor=white)

---

## 📦 Requisitos previos

| Herramienta | Versión mínima | Descarga |
|---|---|---|
| **Python** | 3.10+ | [python.org/downloads](https://www.python.org/downloads/) |
| **Node.js** | 18+ | [nodejs.org](https://nodejs.org/) |
| **pnpm** | cualquiera | `npm install -g pnpm` |
| **Git** | cualquiera | [git-scm.com](https://git-scm.com/) |
| **Docker** | 20+ *(opcional)* | [docs.docker.com/get-docker](https://docs.docker.com/get-docker/) |

> **Verificá las instalaciones:**
> ```bash
> python --version && node --version && pnpm --version
> ```

---

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/CatalinaCorrea-png/Proyecto-Software-2026.git
cd Proyecto-Software-2026
```

### 2. Crear los archivos de variables de entorno

```bash
# Linux / macOS
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

```powershell
# Windows
copy backend\.env.example backend\.env
copy frontend\.env.example frontend\.env
```

> Los valores por defecto funcionan para desarrollo local sin ningún cambio.
> Solo editá `backend/.env` si querés conectar el hardware real (ESP32-CAM).

### 3. Configurar el Backend

```bash
cd backend

# Crear y activar el entorno virtual
python -m venv venv
.\venv\Scripts\Activate.ps1   # Windows PowerShell
# source venv/bin/activate     # Linux / macOS

# Instalar dependencias
pip install -r requirements.txt
```

### 4. Configurar el Frontend

```bash
cd frontend
pnpm install
```

---

## ⚙️ Variables de entorno

Ninguna variable es obligatoria para correr en modo local — todas tienen valores por defecto razonables. Copiá los ejemplos solo si necesitás cambiar algo:

```bash
# Backend
cp backend/.env.example backend/.env

# Frontend
cp frontend/.env.example frontend/.env
```

### Backend (`backend/.env`)

| Variable | Default | Descripción |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./aerosearch.db` | Ruta de la base de datos SQLite |
| `MONGODB_URL` | `mongodb://localhost:27017` | URL de conexión a MongoDB |
| `MONGODB_DB` | `aerosearch` | Nombre de la base de datos |
| `CAMERA_SOURCE` | `synthetic` | Fuente de video: `synthetic`, `webcam`, `esp32`, `video` |
| `DRONE_IP` | — | IP del ESP32-CAM (solo si `CAMERA_SOURCE=esp32`) |
| `ESP32_STREAM_URL` | — | URL del stream (se deriva de `DRONE_IP` si no se define) |
| `DRONE_UDP_PORT` | `4210` | Puerto UDP de recepción |
| `DRONE_UDP_TX_PORT` | `4211` | Puerto UDP de telemetría |
| `VIDEO_SOURCE` | `media/videos/video6.mp4` | Archivo de video local (solo si `CAMERA_SOURCE=video`) |
| `JWT_SECRET_KEY` | *(valor interno)* | Clave secreta para firmar tokens JWT — **cambiar en producción** |
| `JWT_EXPIRE_MINUTES` | `480` | Duración del token en minutos (8 horas por defecto) |

### Frontend (`frontend/.env`)

| Variable | Default | Descripción |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000` | URL base del backend (HTTP) |
| `VITE_WS_URL` | `ws://localhost:8000` | URL base del backend (WebSocket) |

> En Docker las URLs del frontend no necesitan cambiarse — el browser siempre accede al backend en `localhost:8000`.

---

## 🔐 Credenciales de acceso

Al iniciar el backend por primera vez se crean automáticamente dos usuarios:

| Rol | Usuario | Contraseña | Acceso |
|---|---|---|---|
| **ADMIN** | `admin` | `admin123` | Acceso completo (misiones, historial, galería, estadísticas) |
| **USER** | `user` | `user123` | Solo Dashboard (visualización en tiempo real) |

> Las contraseñas se almacenan hasheadas con **bcrypt** en la base de datos.  
> Para producción, cambiá `JWT_SECRET_KEY` en `backend/.env`.

---

## ▶️ Levantar la aplicación

Necesitás **dos terminales** simultáneas.

### Terminal 1 — Backend

```bash
cd backend
.\venv\Scripts\Activate.ps1   # Windows PowerShell
uvicorn main:app --reload
```

Backend disponible en → **http://localhost:8000**  
Documentación interactiva → **http://localhost:8000/docs**

### Terminal 2 — Frontend

```bash
cd frontend
pnpm run dev
```

Frontend disponible en → **http://localhost:5173**

---

## 🐳 Levantar con Docker

```bash
# Levanta MongoDB, backend y frontend
docker compose up

# Solo MongoDB (para desarrollo local del backend)
docker compose up mongodb -d
```

| Servicio | URL |
|---|---|
| Frontend | **http://localhost** |
| Backend (API) | **http://localhost:8000** |
| Swagger (docs) | **http://localhost:8000/docs** |
| MongoDB | `localhost:27017` |

```bash
docker compose logs -f      # Ver logs en tiempo real
docker compose down         # Detener contenedores
docker compose down -v      # Detener y borrar datos de MongoDB
```

---

## 🧪 Tests

El proyecto cuenta con **54 tests de backend** y **34 tests de frontend**.

### Backend

```bash
cd backend
.\venv\Scripts\Activate.ps1
python -m pytest tests/ -v
```

Con reporte de cobertura (genera `coverage/index.html`):

```bash
python -m pytest tests/
```

### Frontend

```bash
cd frontend
pnpm test:run          # Corre los tests una vez
pnpm test              # Modo watch (re-corre al guardar)
pnpm test:coverage     # Genera reporte en coverage/index.html
```

Los tests de CI corren automáticamente en cada PR que toque `backend/` o `frontend/` y publican el reporte de cobertura como comentario.

---

## 🗂️ Estructura del proyecto

```
Proyecto-Software-2026/
├── backend/                        # API REST (FastAPI + Python)
│   ├── main.py                     # Punto de entrada
│   ├── requirements.txt            # Dependencias Python
│   ├── .env.example                # Variables de entorno de ejemplo
│   ├── core/                       # Config y estado global
│   ├── db/                         # Modelos SQLAlchemy y MongoDB
│   ├── modules/
│   │   ├── detection/              # YOLOv8 + detección térmica + fusión
│   │   ├── drone/                  # Telemetría y simulación
│   │   ├── mapping/                # Generación de grilla de búsqueda
│   │   └── storage/                # Persistencia de imágenes
│   ├── routers/                    # Endpoints REST y WebSockets
│   └── tests/                      # Tests unitarios e integración
├── frontend/                       # Dashboard web (React 19 + TypeScript)
│   ├── src/
│   │   ├── config.ts               # URLs del backend (desde .env)
│   │   ├── pages/                  # Dashboard, Historial, Galería, Estadísticas
│   │   ├── components/             # Mapa, cámara, telemetría, alertas
│   │   ├── hooks/                  # WebSocket, misiones, detecciones
│   │   └── types/                  # Tipos TypeScript compartidos
│   ├── .env.example                # Variables de entorno de ejemplo
│   └── package.json
├── hardware/                       # Firmware ESP32-CAM (C++ / PlatformIO)
├── .github/workflows/              # CI: tests + cobertura en cada PR
└── docker-compose.yml
```

---

## 👥 Equipo

| Integrante |
|---|
| Catalina Correa |
| Nicolas Cernadas |
| Dana Cossettini Reyes |
| Maximiliano Andres Bianchimano |
| Fernanda Perez |
| Martin Schubert |
