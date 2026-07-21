import { api } from '@/lib/api'
import type { Project } from '@/features/projects/types'

export async function fetchProjects(): Promise<Project[]> {
  const { data } = await api.get<Project[]>('/projects')
  return data
}

export async function fetchProject(projectId: string): Promise<Project> {
  const { data } = await api.get<Project>(`/projects/${projectId}`)
  return data
}
