import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'

import {
  clearAccessToken,
  getAccessToken,
  setAccessToken,
} from '@/features/auth/session'
import type { TokenResponse } from '@/features/auth/types'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'

export const api = axios.create({
  baseURL: apiBaseUrl,
  withCredentials: true,
  headers: {
    Accept: 'application/json',
  },
})

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

let refreshPromise: Promise<string | null> | null = null

async function refreshAccessToken(): Promise<string | null> {
  try {
    const { data } = await axios.post<TokenResponse>(
      `${apiBaseUrl}/auth/refresh`,
      null,
      { withCredentials: true },
    )
    setAccessToken(data.access_token)
    return data.access_token
  } catch {
    clearAccessToken()
    return null
  }
}

export function ensureAccessToken(): Promise<string | null> {
  if (getAccessToken()) {
    return Promise.resolve(getAccessToken())
  }
  if (!refreshPromise) {
    refreshPromise = refreshAccessToken().finally(() => {
      refreshPromise = null
    })
  }
  return refreshPromise
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as
      | (InternalAxiosRequestConfig & { _retry?: boolean })
      | undefined

    if (
      error.response?.status !== 401 ||
      !original ||
      original._retry ||
      original.url?.includes('/auth/refresh') ||
      original.url?.includes('/auth/google')
    ) {
      return Promise.reject(error)
    }

    original._retry = true
    const token = await ensureAccessToken()
    if (!token) {
      return Promise.reject(error)
    }
    original.headers.Authorization = `Bearer ${token}`
    return api.request(original)
  },
)
