import axios from 'axios'
import { API_URL } from './config'

const TOKEN_KEY = 'aerosearch_token'
const USER_KEY  = 'aerosearch_user'

function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

function clearSession() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
  window.location.reload()
}

// Axios instance with auto-auth and 401 handling
export const apiAxios = axios.create({ baseURL: API_URL })

apiAxios.interceptors.request.use(config => {
  const token = getToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

apiAxios.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) clearSession()
    return Promise.reject(err)
  },
)

// fetch wrapper with auto-auth and 401 handling
export async function apiFetch(input: string, init: RequestInit = {}): Promise<Response> {
  const token = getToken()
  const headers = new Headers(init.headers)
  if (token) headers.set('Authorization', `Bearer ${token}`)
  const res = await fetch(input, { ...init, headers })
  if (res.status === 401) clearSession()
  return res
}
