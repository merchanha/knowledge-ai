import { api } from '@/lib/api'
import type { User } from '@/features/auth/types'

export async function fetchAdminUsers(): Promise<User[]> {
  const { data } = await api.get<User[]>('/admin/users')
  return data
}
