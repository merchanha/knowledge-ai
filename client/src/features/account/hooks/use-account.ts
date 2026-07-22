import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  fetchAccountProjects,
  updateContextExposed,
} from '@/features/account/api/account'

export const accountKeys = {
  all: ['account'] as const,
  projects: ['account', 'projects'] as const,
}

export function useAccountProjects() {
  return useQuery({
    queryKey: accountKeys.projects,
    queryFn: fetchAccountProjects,
  })
}

export function useAccountMutations() {
  const queryClient = useQueryClient()

  const setContextExposed = useMutation({
    mutationFn: ({
      projectId,
      is_context_exposed,
    }: {
      projectId: string
      is_context_exposed: boolean
    }) => updateContextExposed(projectId, is_context_exposed),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: accountKeys.projects })
    },
  })

  return { setContextExposed }
}
