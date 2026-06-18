// Vite expone variables VITE_* via import.meta.env en build time.
// Los defaults apuntan al backend local para desarrollo sin .env.
export const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
export const WS_URL  = import.meta.env.VITE_WS_URL  ?? 'ws://localhost:8000'
