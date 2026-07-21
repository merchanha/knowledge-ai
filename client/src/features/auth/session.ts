/**
 * In-memory access-token session.
 *
 * Why not TanStack Query alone?
 * The JWT from `#token=` is not server state — it is client credentials used by
 * Axios. Interceptors need synchronous access outside React. A tiny module store
 * + useSyncExternalStore is enough; Zustand is not justified here.
 */
import { useSyncExternalStore } from 'react'

let accessToken: string | null = null
const listeners = new Set<() => void>()

function emit(): void {
  for (const listener of listeners) {
    listener()
  }
}

export function getAccessToken(): string | null {
  return accessToken
}

export function setAccessToken(token: string | null): void {
  if (accessToken === token) {
    return
  }
  accessToken = token
  emit()
}

export function clearAccessToken(): void {
  setAccessToken(null)
}

export function subscribeAccessToken(listener: () => void): () => void {
  listeners.add(listener)
  return () => {
    listeners.delete(listener)
  }
}

export function useAccessToken(): string | null {
  return useSyncExternalStore(subscribeAccessToken, getAccessToken, () => null)
}
