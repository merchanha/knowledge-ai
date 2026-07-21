import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { useAuthBootstrap, useCurrentUser } from '@/features/auth/hooks/use-auth'

export function ProtectedRoute() {
  const location = useLocation()
  const { ready, isAuthenticated } = useAuthBootstrap()
  const { isLoading, isError } = useCurrentUser()

  if (!ready || (isAuthenticated && isLoading)) {
    return (
      <div className="flex min-h-dvh items-center justify-center text-muted-foreground">
        Checking session…
      </div>
    )
  }

  if (!isAuthenticated || isError) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  return <Outlet />
}
