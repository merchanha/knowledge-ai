import { useQuery } from '@tanstack/react-query'

import { fetchProject, fetchProjects } from '@/features/projects/api/projects'

export const projectKeys = {
  all: ['projects'] as const,
  detail: (id: string) => ['projects', id] as const,
}

export function useProjects() {
  return useQuery({
    queryKey: projectKeys.all,
    queryFn: fetchProjects,
  })
}

export function useProject(projectId: string | undefined) {
  return useQuery({
    queryKey: projectKeys.detail(projectId ?? ''),
    queryFn: () => fetchProject(projectId!),
    enabled: Boolean(projectId),
  })
}
