export const API = 'http://localhost:8000'

export function getToken(): string {
  return localStorage.getItem('aerosearch_token') || ''
}

export function authHeaders(): Record<string, string> {
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${getToken()}`,
  }
}

export async function authFetch(path: string, options: RequestInit = {}): Promise<Response> {
  return fetch(`${API}${path}`, {
    ...options,
    headers: { ...authHeaders(), ...(options.headers as Record<string, string> || {}) },
  })
}
