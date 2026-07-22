import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  addProjectMember,
  archiveProject,
  createProject,
  deleteProject,
  fetchProject,
  fetchProjectMembers,
  fetchProjects,
  removeProjectMember,
  unarchiveProject,
  updateProject,
} from '@/features/projects/api/projects'
import type { ProjectMembershipRole } from '@/features/account/types'

export const projectKeys = {
  all: ['projects'] as const,
  detail: (id: string) => ['projects', id] as const,
  members: (id: string) => ['projects', id, 'members'] as const,
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

export function useProjectMembers(projectId: string | undefined) {
  return useQuery({
    queryKey: projectKeys.members(projectId ?? ''),
    queryFn: () => fetchProjectMembers(projectId!),
    enabled: Boolean(projectId),
  })
}

export function useProjectMutations() {
  const queryClient = useQueryClient()

  const invalidateAll = () => {
    void queryClient.invalidateQueries({ queryKey: projectKeys.all })
  }

  const invalidateDetail = (projectId: string) => {
    void queryClient.invalidateQueries({
      queryKey: projectKeys.detail(projectId),
    })
    invalidateAll()
  }

  const create = useMutation({
    mutationFn: createProject,
    onSuccess: () => invalidateAll(),
  })

  const update = useMutation({
    mutationFn: ({
      projectId,
      body,
    }: {
      projectId: string
      body: { name?: string; description?: string | null }
    }) => updateProject(projectId, body),
    onSuccess: (_data, vars) => invalidateDetail(vars.projectId),
  })

  const remove = useMutation({
    mutationFn: (projectId: string) => deleteProject(projectId),
    onSuccess: () => invalidateAll(),
  })

  const archive = useMutation({
    mutationFn: (projectId: string) => archiveProject(projectId),
    onSuccess: (_data, projectId) => invalidateDetail(projectId),
  })

  const unarchive = useMutation({
    mutationFn: (projectId: string) => unarchiveProject(projectId),
    onSuccess: (_data, projectId) => invalidateDetail(projectId),
  })

  const addMember = useMutation({
    mutationFn: ({
      projectId,
      userId,
      role,
    }: {
      projectId: string
      userId: string
      role?: ProjectMembershipRole
    }) => addProjectMember(projectId, { user_id: userId, role }),
    onSuccess: (_data, vars) => {
      void queryClient.invalidateQueries({
        queryKey: projectKeys.members(vars.projectId),
      })
    },
  })

  const removeMember = useMutation({
    mutationFn: ({
      projectId,
      userId,
    }: {
      projectId: string
      userId: string
    }) => removeProjectMember(projectId, userId),
    onSuccess: (_data, vars) => {
      void queryClient.invalidateQueries({
        queryKey: projectKeys.members(vars.projectId),
      })
    },
  })

  return {
    create,
    update,
    remove,
    archive,
    unarchive,
    addMember,
    removeMember,
  }
}
