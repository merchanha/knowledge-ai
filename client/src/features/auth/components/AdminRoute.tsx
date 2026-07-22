import { Navigate, Outlet } from 'react-router-dom'

import { LoadingState } from '@/components/LoadingState'
import { useCurrentUser } from '@/features/auth/hooks/use-auth'

/** Renders children only when the signed-in user has role `admin`. */
export function AdminRoute() {
  const { data: me, isLoading, isError } = useCurrentUser()

  if (isLoading) {
    return <LoadingState label="Checking permissions…" />
  }

  if (isError || me?.role !== 'admin') {
    return <Navigate to="/projects" replace />
  }

  return <Outlet />
}
