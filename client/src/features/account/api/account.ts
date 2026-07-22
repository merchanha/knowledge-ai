import { api } from '@/lib/api'
import type { AccountProject, Membership } from '@/features/account/types'

export async function fetchAccountProjects(): Promise<AccountProject[]> {
  const { data } = await api.get<AccountProject[]>('/account')
  return data
}

export async function updateContextExposed(
  projectId: string,
  is_context_exposed: boolean,
): Promise<Membership> {
  const { data } = await api.patch<Membership>(`/account/projects/${projectId}`, {
    is_context_exposed,
  })
  return data
}
