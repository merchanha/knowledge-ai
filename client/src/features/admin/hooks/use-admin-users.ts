import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  fetchAdminUsers,
  updateAdminUser,
} from '@/features/admin/api/users'
import { useCurrentUser } from '@/features/auth/hooks/use-auth'
import type { UserRole } from '@/features/auth/types'

export const adminUserKeys = {
  all: ['admin', 'users'] as const,
}

export function useAdminUsers(enabled: boolean) {
  const { data: me } = useCurrentUser()
  const isAdmin = me?.role === 'admin'

  return useQuery({
    queryKey: adminUserKeys.all,
    queryFn: fetchAdminUsers,
    enabled: enabled && isAdmin,
  })
}

export function useAdminUserMutations() {
  const queryClient = useQueryClient()

  const update = useMutation({
    mutationFn: ({
      userId,
      body,
    }: {
      userId: string
      body: { role?: UserRole; is_active?: boolean }
    }) => updateAdminUser(userId, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: adminUserKeys.all })
    },
  })

  return { update }
}
