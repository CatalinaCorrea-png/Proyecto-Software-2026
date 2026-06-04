<div align="center">

# Proyecto Software 2026

**Aplicación web full-stack con visión artificial, análisis de datos en tiempo real y visualización interactiva.**

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
- [Levantar la aplicación](#-levantar-la-aplicación)
- [Levantar con Docker](#-levantar-con-docker)
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

Antes de comenzar, descargá e instalá las siguientes herramientas:

| Herramienta | Versión mínima | Descarga |
|---|---|---|
| **Python** | 3.10+ | [python.org/downloads](https://www.python.org/downloads/) |
| **Node.js** | 18+ | [nodejs.org](https://nodejs.org/) |
| **pnpm** | cualquiera | `npm install -g pnpm` |
| **Git** | cualquiera | [git-scm.com](https://git-scm.com/) |
| **Docker** | 20+ *(opcional)* | [docs.docker.com/get-docker](https://docs.docker.com/get-docker/) |

> **Verificá las instalaciones** ejecutando en tu terminal:
> ```bash
> python --version
> node --version
> pnpm --version
> git --version
> ```

---

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/CatalinaCorrea-png/Proyecto-Software-2026.git
cd Proyecto-Software-2026
```

### 2. Configurar el Backend

```bash
# Moverse a la carpeta del backend
cd backend

# Crear el entorno virtual
python -m venv venv
```

**Activar el entorno virtual:**

```bash
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Windows (CMD)
venv\Scripts\activate.bat
```

> Cuando el entorno está activo, vas a ver `(venv)` al inicio de la línea en tu terminal.

```bash
# Instalar dependencias de Python
pip install -r requirements.txt
```

### 3. Configurar el Frontend

```bash
# Desde la raíz del proyecto, moverse a la carpeta del frontend
cd frontend

# Instalar dependencias de Node.js
pnpm install
```

---

## ▶️ Levantar la aplicación

Necesitás **dos terminales abiertas** al mismo tiempo — una para el backend y otra para el frontend.

### Terminal 1 — Backend

```bash
cd backend
.\venv\Scripts\Activate.ps1   # Windows PowerShell
uvicorn main:app --reload
```

El backend queda disponible en → **http://localhost:8000**  
Documentación de la API (Swagger) → **http://localhost:8000/docs**

### Terminal 2 — Frontend

```bash
cd frontend
pnpm run dev
```

El frontend queda disponible en → **http://localhost:5173**

---

## 🐳 Levantar con Docker

### Variables de entorno

El archivo `backend/.env` está ignorado por Git — los valores de tu entorno no se suben al repositorio. Para saber qué configurar, usá `backend/.env.example` como referencia:

```bash
cp backend/.env.example backend/.env   # Linux / macOS
copy backend\.env.example backend\.env # Windows
```

Las variables de hardware (IP del drone, URL del stream) **no tienen default en el código** — si usás el ESP32-CAM tenés que definirlas en `.env`. El resto tiene valores por defecto razonables y no hace falta tocarlos salvo que necesites cambiarlos.

| Variable | Default | Requerido |
|---|---|---|
| `CAMERA_SOURCE` | `webcam` | No |
| `DRONE_IP` | — | Solo si `CAMERA_SOURCE=esp32` |
| `ESP32_STREAM_URL` | — | Solo si `CAMERA_SOURCE=esp32` |
| `DRONE_UDP_PORT` | `4210` | No |
| `DRONE_UDP_TX_PORT` | `4211` | No |
| `MONGODB_URL` | `mongodb://localhost:27017` | No (Docker lo sobreescribe automáticamente) |
| `MONGODB_DB` | `aerosearch` | No |

### Comando

```bash
# Desde la raíz del proyecto — levanta MongoDB
docker compose up mongodb -d
```

Una vez que termine, los servicios quedan disponibles en:

| Servicio | URL |
|---|---|
| Frontend | **http://localhost** |
| Backend (API) | **http://localhost:8000** |
| Swagger (docs) | **http://localhost:8000/docs** |
| MongoDB | `localhost:27017` |

> La primera vez tarda más porque descarga las imágenes base y construye los contenedores.

### Otros comandos útiles

```bash
# Ver los logs en tiempo real
docker compose logs -f

# Detener todos los contenedores
docker compose down

# Detener y eliminar los volúmenes (borra los datos de MongoDB)
docker compose down -v
```

---

## 🗂️ Estructura del proyecto

```
Proyecto-Software-2026/
├── backend/                # API REST en Python (FastAPI)
│   ├── main.py             # Punto de entrada del servidor
│   ├── requirements.txt    # Dependencias de Python
│   └── ...
├── frontend/               # Interfaz web en TypeScript + React
│   ├── src/
│   ├── package.json
│   └── ...
└── README.md
```

## 👥 Equipo

| Integrante |
|---|
| Catalina Correa |
| Nicolas Cernadas |
| Dana Cossettini Reyes |
| Maximiliano Andres Bianchimano |
| Fernanda Perez |
| Martin Schubert |

