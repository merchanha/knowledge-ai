import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useEffect } from 'react'

import {
  useAuthBootstrap,
  useCurrentUser,
} from '@/features/auth/hooks/use-auth'
import { clearAccessToken } from '@/features/auth/session'

export function ProtectedRoute() {
  const location = useLocation()
  const { ready, isAuthenticated } = useAuthBootstrap()
  const { isLoading, isError, error } = useCurrentUser()

  useEffect(() => {
    if (isError) {
      // Drop dead Bearer so /login does not treat us as signed in.
      clearAccessToken()
    }
  }, [isError])

  if (!ready || (isAuthenticated && isLoading)) {
    return (
      <div className="flex min-h-dvh items-center justify-center text-muted-foreground">
        Checking session…
      </div>
    )
  }

  if (!isAuthenticated || isError) {
    return (
      <Navigate
        to="/login"
        replace
        state={{
          from: location.pathname,
          sessionExpired: isError,
          reason: isError
            ? ((error as Error)?.message ?? 'Invalid or expired token')
            : undefined,
        }}
      />
    )
  }

  return <Outlet />
}
