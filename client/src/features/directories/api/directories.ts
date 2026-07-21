import { api } from '@/lib/api'
import type {
  Directory,
  DirectoryPermission,
  DirectoryPermissionEntry,
} from '@/features/directories/types'

export async function fetchDirectoryTree(projectId: string): Promise<Directory[]> {
  const { data } = await api.get<Directory[]>(
    `/projects/${projectId}/directories/tree`,
  )
  return data
}

export async function fetchBreadcrumbs(directoryId: string): Promise<Directory[]> {
  const { data } = await api.get<Directory[]>(
    `/directories/${directoryId}/breadcrumbs`,
  )
  return data
}

export async function createChildDirectory(
  parentId: string,
  name: string,
): Promise<Directory> {
  const { data } = await api.post<Directory>(`/directories/${parentId}/children`, {
    name,
  })
  return data
}

export async function renameDirectory(
  directoryId: string,
  name: string,
): Promise<Directory> {
  const { data } = await api.patch<Directory>(`/directories/${directoryId}`, {
    name,
  })
  return data
}

export async function moveDirectory(
  directoryId: string,
  newParentId: string,
): Promise<Directory> {
  const { data } = await api.patch<Directory>(`/directories/${directoryId}/move`, {
    new_parent_id: newParentId,
  })
  return data
}

export async function deleteDirectory(directoryId: string): Promise<void> {
  await api.delete(`/directories/${directoryId}`)
}

export async function grantDirectoryPermission(
  directoryId: string,
  userId: string,
  permission: DirectoryPermission,
): Promise<void> {
  await api.post(`/permissions/directories/${directoryId}`, {
    user_id: userId,
    permission,
  })
}

export async function revokeDirectoryPermission(
  directoryId: string,
  userId: string,
  permission: DirectoryPermission,
): Promise<void> {
  await api.delete(`/permissions/directories/${directoryId}`, {
    data: { user_id: userId, permission },
  })
}

export async function fetchMyPermissions(): Promise<DirectoryPermissionEntry[]> {
  const { data } = await api.get<{ permissions: DirectoryPermissionEntry[] }>(
    '/permissions/me',
  )
  return data.permissions
}
