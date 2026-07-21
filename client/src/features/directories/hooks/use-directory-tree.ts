import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  createChildDirectory,
  deleteDirectory,
  fetchBreadcrumbs,
  fetchDirectoryTree,
  grantDirectoryPermission,
  moveDirectory,
  renameDirectory,
  revokeDirectoryPermission,
} from '@/features/directories/api/directories'
import type { DirectoryPermission } from '@/features/directories/types'
import { buildDirectoryTree } from '@/features/directories/utils/tree'

export const directoryKeys = {
  tree: (projectId: string) => ['directories', 'tree', projectId] as const,
  breadcrumbs: (directoryId: string) =>
    ['directories', 'breadcrumbs', directoryId] as const,
}

export function useDirectoryTree(projectId: string | undefined) {
  const query = useQuery({
    queryKey: directoryKeys.tree(projectId ?? ''),
    queryFn: () => fetchDirectoryTree(projectId!),
    enabled: Boolean(projectId),
  })

  return {
    ...query,
    flat: query.data ?? [],
    tree: query.data ? buildDirectoryTree(query.data) : [],
  }
}

export function useBreadcrumbs(directoryId: string | undefined) {
  return useQuery({
    queryKey: directoryKeys.breadcrumbs(directoryId ?? ''),
    queryFn: () => fetchBreadcrumbs(directoryId!),
    enabled: Boolean(directoryId),
  })
}

function useInvalidateTree(projectId: string | undefined) {
  const queryClient = useQueryClient()
  return () => {
    if (!projectId) return
    void queryClient.invalidateQueries({
      queryKey: directoryKeys.tree(projectId),
    })
  }
}

export function useDirectoryMutations(projectId: string | undefined) {
  const invalidate = useInvalidateTree(projectId)
  const queryClient = useQueryClient()

  const createChild = useMutation({
    mutationFn: ({ parentId, name }: { parentId: string; name: string }) =>
      createChildDirectory(parentId, name),
    onSuccess: () => invalidate(),
  })

  const rename = useMutation({
    mutationFn: ({ directoryId, name }: { directoryId: string; name: string }) =>
      renameDirectory(directoryId, name),
    onSuccess: (_data, vars) => {
      invalidate()
      void queryClient.invalidateQueries({
        queryKey: directoryKeys.breadcrumbs(vars.directoryId),
      })
    },
  })

  const move = useMutation({
    mutationFn: ({
      directoryId,
      newParentId,
    }: {
      directoryId: string
      newParentId: string
    }) => moveDirectory(directoryId, newParentId),
    onSuccess: (_data, vars) => {
      invalidate()
      void queryClient.invalidateQueries({
        queryKey: directoryKeys.breadcrumbs(vars.directoryId),
      })
    },
  })

  const remove = useMutation({
    mutationFn: (directoryId: string) => deleteDirectory(directoryId),
    onSuccess: () => invalidate(),
  })

  const grantPermission = useMutation({
    mutationFn: ({
      directoryId,
      userId,
      permission,
    }: {
      directoryId: string
      userId: string
      permission: DirectoryPermission
    }) => grantDirectoryPermission(directoryId, userId, permission),
  })

  const revokePermission = useMutation({
    mutationFn: ({
      directoryId,
      userId,
      permission,
    }: {
      directoryId: string
      userId: string
      permission: DirectoryPermission
    }) => revokeDirectoryPermission(directoryId, userId, permission),
  })

  return {
    createChild,
    rename,
    move,
    remove,
    grantPermission,
    revokePermission,
  }
}
