import { api } from '@/lib/api'
import type { User, UserRole } from '@/features/auth/types'

export async function fetchAdminUsers(): Promise<User[]> {
  const { data } = await api.get<User[]>('/admin/users')
  return data
}

export async function updateAdminUser(
  userId: string,
  body: { role?: UserRole; is_active?: boolean },
): Promise<User> {
  const { data } = await api.patch<User>(`/admin/users/${userId}`, body)
  return data
}
