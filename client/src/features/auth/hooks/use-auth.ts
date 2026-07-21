import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import {
  fetchCurrentUser,
  logoutRequest,
  startGoogleLogin,
} from '@/features/auth/api/auth'
import {
  clearAccessToken,
  setAccessToken,
  useAccessToken,
} from '@/features/auth/session'
import type { User } from '@/features/auth/types'
import { ensureAccessToken } from '@/lib/api'

export const authKeys = {
  me: ['auth', 'me'] as const,
}

export function useCurrentUser() {
  const token = useAccessToken()

  return useQuery({
    queryKey: authKeys.me,
    queryFn: fetchCurrentUser,
    enabled: Boolean(token),
    staleTime: 60_000,
  })
}

export function useAuthBootstrap() {
  const token = useAccessToken()
  const [ready, setReady] = useState(false)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      if (!token) {
        await ensureAccessToken()
      }
      if (!cancelled) {
        setReady(true)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [token])

  return { ready, isAuthenticated: Boolean(token) }
}

export function useAuth() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const token = useAccessToken()
  const userQuery = useCurrentUser()

  const login = useCallback(() => {
    startGoogleLogin()
  }, [])

  const acceptFragmentToken = useCallback((accessToken: string) => {
    setAccessToken(accessToken)
  }, [])

  const logout = useMutation({
    mutationFn: async () => {
      try {
        await logoutRequest()
      } finally {
        clearAccessToken()
        queryClient.clear()
      }
    },
    onSuccess: () => {
      navigate('/login', { replace: true })
    },
  })

  return {
    token,
    isAuthenticated: Boolean(token),
    user: userQuery.data as User | undefined,
    isLoadingUser: userQuery.isLoading,
    userError: userQuery.error,
    login,
    acceptFragmentToken,
    logout: () => logout.mutate(),
    isLoggingOut: logout.isPending,
  }
}
