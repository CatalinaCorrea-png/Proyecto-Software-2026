import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react'

export type Role = 'ADMIN' | 'USER' | 'GUEST'

export interface UserInfo {
  username: string
  role: Role
}

interface AuthContextValue {
  user: UserInfo | null
  token: string | null
  login: (username: string, role: string, token: string) => void
  loginAsGuest: () => void
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

const TOKEN_KEY = 'aerosearch_token'
const USER_KEY  = 'aerosearch_user'

// Modo invitado: mismo usuario "virtual" tanto si se entra por el botón de
// login como por el enlace compartible (evita duplicar la definición).
const GUEST_INFO: UserInfo = { username: 'Invitado', role: 'GUEST' }

// Parámetro del enlace compartible de modo lectura (?guest=1). Un Administrador
// lo genera desde la barra de navegación para dar acceso de solo-visualización
// sin pasar por el login ni el panel administrativo.
const GUEST_LINK_PARAM = 'guest'

export function isGuestLinkVisit(): boolean {
  try {
    return new URLSearchParams(window.location.search).get(GUEST_LINK_PARAM) === '1'
  } catch {
    return false
  }
}

export function buildGuestLink(): string {
  return `${window.location.origin}${window.location.pathname}?${GUEST_LINK_PARAM}=1`
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY))
  const [user, setUser] = useState<UserInfo | null>(() => {
    try {
      const stored = localStorage.getItem(USER_KEY)
      if (stored) return JSON.parse(stored) as UserInfo
      // Enlace compartido de modo lectura: entra directo como invitado, sin
      // login ni token, igual que "Entrar como invitado". No pisa una sesión
      // ya logueada en este navegador (solo aplica si no había nada guardado).
      if (isGuestLinkVisit()) {
        localStorage.setItem(USER_KEY, JSON.stringify(GUEST_INFO))
        return GUEST_INFO
      }
      return null
    } catch {
      return null
    }
  })

  // Una vez consumido el enlace compartible, limpiamos el parámetro de la URL:
  // no queremos reprocesarlo en cada refresh ni dejarlo pegado en la barra
  // de direcciones (la sesión de invitado ya quedó guardada en localStorage).
  useEffect(() => {
    if (isGuestLinkVisit()) {
      const url = new URL(window.location.href)
      url.searchParams.delete(GUEST_LINK_PARAM)
      window.history.replaceState({}, '', url)
    }
  }, [])

  const login = useCallback((username: string, role: string, accessToken: string) => {
    const info: UserInfo = { username, role: role as Role }
    localStorage.setItem(TOKEN_KEY, accessToken)
    localStorage.setItem(USER_KEY, JSON.stringify(info))
    setToken(accessToken)
    setUser(info)
  }, [])

  // Modo invitado: entra sin credenciales ni token. Solo lectura.
  // Persistimos el usuario (no hay token) para que sobreviva un refresh.
  const loginAsGuest = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.setItem(USER_KEY, JSON.stringify(GUEST_INFO))
    setToken(null)
    setUser(GUEST_INFO)
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    setToken(null)
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, token, login, loginAsGuest, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
