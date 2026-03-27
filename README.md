# 🚀 Proyecto Software 2026

Aplicación web full-stack con backend en **Python** y frontend en **TypeScript/React**.

---

## 📋 Requisitos previos

Antes de comenzar, asegurate de tener instalado:

- [Python 3.10+](https://www.python.org/downloads/)
- [Node.js 18+](https://nodejs.org/)
- [Git](https://git-scm.com/)

---

## 📥 Clonar el repositorio

```bash
git clone https://github.com/CatalinaCorrea-png/Proyecto-Software-2026.git
cd Proyecto-Software-2026
```

---

## ⚙️ Backend (Python)

### 1. Moverse a la carpeta del backend

```bash
cd backend
```

### 2. Crear y activar un entorno virtual (PowerShell)

```bash
# Crear el entorno virtual
python -m venv venv

# Activar en Linux/macOS
source venv/bin/activate

# Activar en Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Activar en Windows (CMD)
venv\Scripts\activate.bat
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```
### 4. Levantar el servidor backend

```bash
uvicorn main:app --reload
```

> El backend estará disponible en `http://localhost:8000`

---

## 🖥️ Frontend (TypeScript / React)

### 1. Abrí una nueva terminal y moverse a la carpeta del frontend

```bash
cd frontend
```

### 2. Instalar dependencias

```bash
pnpm install
```
### 3. Levantar el servidor de desarrollo

```bash
pnpm run dev
```

> El frontend estará disponible en `http://localhost:5173`

---

## 🗂️ Estructura del proyecto

```
Proyecto-Software-2026/
├── backend/          # API en Python (FastAPI)
│   ├── requirements.txt
│   └── ...
├── frontend/         # Interfaz en TypeScript/React
│   ├── package.json
│   └── ...
└── README.md
```

---

## 🐛 Solución de problemas comunes

| Problema | Solución |
|---|---|
| `ModuleNotFoundError` en Python | Asegurate de tener el entorno virtual activado y haber ejecutado `pip install -r requirements.txt` |
| `npm: command not found` | Instalá [Node.js](https://nodejs.org/) y verificá con `node -v` |
| Error de CORS | Verificá que la URL del backend en el `.env` del frontend sea correcta |
| Puerto en uso | Cambiá el puerto: `uvicorn main:app --port 8001` o `npm run dev -- --port 3001` |

---

## 🤝 Proyecto desarrollado en equipo

- Catalina Correa
- Nicolas Cernadas
- Dana Cossettini Reyes
- Maximiliano Andres Bianchimano
- Fernanda Perez
- Martin Schubert

---