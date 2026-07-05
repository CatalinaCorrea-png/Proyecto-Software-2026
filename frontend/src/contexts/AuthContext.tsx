import { createContext, useContext, useState, useCallback, type ReactNode } from 'react'

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

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY))
  const [user, setUser] = useState<UserInfo | null>(() => {
    try {
      const s = localStorage.getItem(USER_KEY)
      return s ? (JSON.parse(s) as UserInfo) : null
    } catch {
      return null
    }
  })

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
    const info: UserInfo = { username: 'Invitado', role: 'GUEST' }
    localStorage.removeItem(TOKEN_KEY)
    localStorage.setItem(USER_KEY, JSON.stringify(info))
    setToken(null)
    setUser(info)
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
