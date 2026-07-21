import { api } from '@/lib/api'
import type { TokenResponse, User } from '@/features/auth/types'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'
const spaOrigin = import.meta.env.VITE_SPA_ORIGIN ?? window.location.origin

export function getOAuthCallbackUrl(): string {
  return `${spaOrigin}/auth/callback`
}

/** Full-page redirect into Google OAuth via the FastAPI login endpoint. */
export function startGoogleLogin(): void {
  const redirectUri = encodeURIComponent(getOAuthCallbackUrl())
  window.location.assign(`${apiBaseUrl}/auth/google/login?redirect_uri=${redirectUri}`)
}

export async function fetchCurrentUser(): Promise<User> {
  const { data } = await api.get<User>('/auth/me')
  return data
}

export async function logoutRequest(): Promise<void> {
  await api.post('/auth/logout')
}

export async function refreshRequest(): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>('/auth/refresh')
  return data
}
