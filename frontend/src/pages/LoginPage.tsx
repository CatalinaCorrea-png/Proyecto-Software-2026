import { useState } from 'react'
import { API_URL } from '../config'
import { useAuth } from '../contexts/AuthContext'
import { GlobeHero } from '../components/hero/GlobeHero'
import { WebGLStars } from '../components/hero/WebGLStars'

export function LoginPage() {
  const { login, loginAsGuest } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        setError((data as { detail?: string }).detail || 'Credenciales inválidas')
        return
      }
      const data = await res.json() as { access_token: string; username: string; role: string }
      login(data.username, data.role, data.access_token)
    } catch {
      setError('Error de conexión con el servidor')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      {/* Fondo de estrellas WebGL: fijo a pantalla completa, detrás de todo. */}
      <WebGLStars />
      {/* Globo: elemento libre grande, detrás del modal, corrido a la derecha
          e inclinado. No está contenido en ninguna caja. */}
      <div className="login-globe-bg" aria-hidden="true">
        <GlobeHero />
      </div>
      {/* Modal de login centrado en la pantalla. */}
      <div className="login-container">
        <div className="login-card login-card--modal">
        <div className="login-brand">AeroSearch AI</div>
        <p className="login-subtitle">Sistema de Búsqueda y Rescate con Drones</p>
        <form onSubmit={handleSubmit} className="login-form">
          <div className="login-field">
            <label htmlFor="username">Usuario</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              placeholder="Ingresa tu usuario"
              required
              autoComplete="username"
            />
          </div>
          <div className="login-field">
            <label htmlFor="password">Contraseña</label>
            <div className="login-password-wrapper">
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                autoComplete="current-password"
              />
              <button
                type="button"
                className="login-eye"
                onClick={() => setShowPassword(v => !v)}
                tabIndex={-1}
                aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
              >
                {showPassword ? (
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                    <circle cx="12" cy="12" r="3"/>
                  </svg>
                ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/>
                    <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/>
                    <line x1="1" y1="1" x2="23" y2="23"/>
                  </svg>
                )}
              </button>
            </div>
          </div>
          {error && <div className="login-error">{error}</div>}
          <button type="submit" className="login-btn" disabled={loading}>
            {loading ? 'Ingresando...' : 'Ingresar'}
          </button>
        </form>

        <div className="login-divider">solo lectura</div>
        <button type="button" className="login-guest-btn" onClick={loginAsGuest}>
          Entrar como invitado
        </button>
        </div>
      </div>
    </>
  )
}
