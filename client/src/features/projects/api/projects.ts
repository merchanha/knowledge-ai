import { api } from '@/lib/api'
import type { Membership, ProjectMembershipRole } from '@/features/account/types'
import type { Project } from '@/features/projects/types'

export async function fetchProjects(): Promise<Project[]> {
  const { data } = await api.get<Project[]>('/projects')
  return data
}

export async function fetchProject(projectId: string): Promise<Project> {
  const { data } = await api.get<Project>(`/projects/${projectId}`)
  return data
}

export async function createProject(body: {
  name: string
  description?: string | null
}): Promise<Project> {
  const { data } = await api.post<Project>('/projects', body)
  return data
}

export async function updateProject(
  projectId: string,
  body: { name?: string; description?: string | null },
): Promise<Project> {
  const { data } = await api.patch<Project>(`/projects/${projectId}`, body)
  return data
}

export async function deleteProject(projectId: string): Promise<void> {
  await api.delete(`/projects/${projectId}`)
}

export async function archiveProject(projectId: string): Promise<Project> {
  const { data } = await api.post<Project>(`/projects/${projectId}/archive`)
  return data
}

export async function unarchiveProject(projectId: string): Promise<Project> {
  const { data } = await api.post<Project>(`/projects/${projectId}/unarchive`)
  return data
}

export async function fetchProjectMembers(
  projectId: string,
): Promise<Membership[]> {
  const { data } = await api.get<Membership[]>(`/projects/${projectId}/members`)
  return data
}

export async function addProjectMember(
  projectId: string,
  body: { user_id: string; role?: ProjectMembershipRole },
): Promise<Membership> {
  const { data } = await api.post<Membership>(
    `/projects/${projectId}/members`,
    body,
  )
  return data
}

export async function removeProjectMember(
  projectId: string,
  userId: string,
): Promise<void> {
  await api.delete(`/projects/${projectId}/members/${userId}`)
}
