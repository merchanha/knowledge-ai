import { useQuery } from '@tanstack/react-query'

import { fetchAdminUsers } from '@/features/admin/api/users'
import { useCurrentUser } from '@/features/auth/hooks/use-auth'

export function useAdminUsers(enabled: boolean) {
  const { data: me } = useCurrentUser()
  const isAdmin = me?.role === 'admin'

  return useQuery({
    queryKey: ['admin', 'users'],
    queryFn: fetchAdminUsers,
    enabled: enabled && isAdmin,
  })
}
