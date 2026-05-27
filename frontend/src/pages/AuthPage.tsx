import { useState } from 'react'

const API = 'http://localhost:8000'

interface Props {
  onLogin: (token: string, email: string) => void
}

function EyeIcon({ open }: { open: boolean }) {
  return open ? (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19" />
      <line x1="1" y1="1" x2="23" y2="23" />
    </svg>
  ) : (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  )
}

export function AuthPage({ onLogin }: Props) {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const validateEmail = (v: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)

  const switchMode = (m: 'login' | 'register') => {
    setMode(m)
    setError('')
    setPassword('')
    setConfirmPassword('')
    setShowPassword(false)
    setShowConfirm(false)
  }

  const handleLogin = async () => {
    setError('')
    if (!email || !password) { setError('Completá todos los campos'); return }
    if (!validateEmail(email)) { setError('El email no es válido'); return }
    setLoading(true)
    try {
      const res = await fetch(`${API}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || `Error ${res.status}`)
      onLogin(data.access_token, data.email)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e)
      setError(msg || 'Error de conexión')
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async () => {
    setError('')
    if (!email || !password || !confirmPassword) { setError('Completá todos los campos'); return }
    if (!validateEmail(email)) { setError('El email no es válido'); return }
    if (password.length < 6) { setError('La contraseña debe tener al menos 6 caracteres'); return }
    if (password !== confirmPassword) { setError('Las contraseñas no coinciden'); return }
    setLoading(true)
    try {
      const res = await fetch(`${API}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || `Error ${res.status}`)
      onLogin(data.access_token, data.email)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e)
      setError(msg || 'Error de conexión')
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      if (mode === 'login') handleLogin()
      else handleRegister()
    }
  }

  const inputStyle: React.CSSProperties = {
    background: '#0A1628',
    border: '1px solid #1E3A5F',
    borderRadius: 4,
    color: '#E0E0E0',
    fontFamily: 'monospace',
    fontSize: 13,
    padding: '7px 10px',
    width: '100%',
    outline: 'none',
    boxSizing: 'border-box',
  }

  const labelStyle: React.CSSProperties = {
    color: '#78909C',
    fontSize: 10,
    fontFamily: 'monospace',
    letterSpacing: 1,
    marginBottom: 4,
  }

  const eyeBtnStyle: React.CSSProperties = {
    position: 'absolute',
    right: 8,
    top: '50%',
    transform: 'translateY(-50%)',
    background: 'transparent',
    border: 'none',
    color: '#546E7A',
    cursor: 'pointer',
    padding: 0,
    display: 'flex',
    alignItems: 'center',
  }

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100vh',
      background: '#0A0E1A',
      padding: 20,
    }}>
      <div style={{
        background: '#0D1B2A',
        border: '1px solid #1E3A5F',
        borderRadius: 8,
        padding: '28px 32px',
        width: 380,
        display: 'flex',
        flexDirection: 'column',
        gap: 16,
      }}>

        {/* Header */}
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 22, fontWeight: 'bold', color: '#FF6D00', fontFamily: 'monospace' }}>
            AeroSearch AI
          </div>
          <div style={{ fontSize: 10, color: '#546E7A', fontFamily: 'monospace', marginTop: 3, letterSpacing: 1 }}>
            SISTEMA DE BÚSQUEDA Y RESCATE
          </div>
        </div>

        {/* Mode tabs */}
        <div style={{ display: 'flex', borderBottom: '1px solid #1E3A5F', marginBottom: 4 }}>
          {(['login', 'register'] as const).map(m => (
            <button
              key={m}
              onClick={() => switchMode(m)}
              style={{
                flex: 1,
                background: 'transparent',
                border: 'none',
                borderBottom: `2px solid ${mode === m ? '#FF6D00' : 'transparent'}`,
                color: mode === m ? '#FF6D00' : '#546E7A',
                fontFamily: 'monospace',
                fontSize: 10,
                letterSpacing: 1,
                padding: '8px 0',
                cursor: 'pointer',
                transition: 'all 0.2s',
                marginBottom: -1,
              }}
            >
              {m === 'login' ? 'INICIAR SESIÓN' : 'REGISTRARSE'}
            </button>
          ))}
        </div>

        {/* Email */}
        <div>
          <div style={labelStyle}>EMAIL</div>
          <input
            type="email"
            style={inputStyle}
            placeholder="usuario@ejemplo.com"
            value={email}
            onChange={e => setEmail(e.target.value)}
            onKeyDown={handleKeyDown}
            autoComplete="email"
          />
        </div>

        {/* Password */}
        <div>
          <div style={labelStyle}>CONTRASEÑA</div>
          <div style={{ position: 'relative' }}>
            <input
              type={showPassword ? 'text' : 'password'}
              style={{ ...inputStyle, paddingRight: 36 }}
              placeholder={mode === 'register' ? 'Mínimo 6 caracteres' : '••••••••'}
              value={password}
              onChange={e => setPassword(e.target.value)}
              onKeyDown={mode === 'login' ? handleKeyDown : undefined}
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
            />
            <button type="button" style={eyeBtnStyle} onClick={() => setShowPassword(v => !v)}>
              <EyeIcon open={showPassword} />
            </button>
          </div>
        </div>

        {/* Confirm password — register only */}
        {mode === 'register' && (
          <div>
            <div style={labelStyle}>CONFIRMAR CONTRASEÑA</div>
            <div style={{ position: 'relative' }}>
              <input
                type={showConfirm ? 'text' : 'password'}
                style={{ ...inputStyle, paddingRight: 36 }}
                placeholder="Repetí tu contraseña"
                value={confirmPassword}
                onChange={e => setConfirmPassword(e.target.value)}
                onKeyDown={handleKeyDown}
                autoComplete="new-password"
              />
              <button type="button" style={eyeBtnStyle} onClick={() => setShowConfirm(v => !v)}>
                <EyeIcon open={showConfirm} />
              </button>
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div style={{ color: '#FF5252', fontSize: 11, fontFamily: 'monospace', textAlign: 'center' }}>
            {error}
          </div>
        )}

        {/* Submit */}
        <button
          onClick={mode === 'login' ? handleLogin : handleRegister}
          disabled={loading}
          style={{
            background: loading ? '#37474F' : '#FF6D00',
            color: '#fff',
            border: 'none',
            borderRadius: 6,
            padding: '10px 0',
            fontSize: 13,
            fontFamily: 'monospace',
            fontWeight: 'bold',
            letterSpacing: 1,
            cursor: loading ? 'wait' : 'pointer',
            transition: 'background 0.2s',
            width: '100%',
          }}
        >
          {loading ? 'PROCESANDO...' : mode === 'login' ? 'INGRESAR' : 'CREAR CUENTA'}
        </button>
      </div>
    </div>
  )
}
