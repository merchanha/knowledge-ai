import { useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { EmptyState } from '@/components/EmptyState'
import { LoadingState } from '@/components/LoadingState'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Separator } from '@/components/ui/separator'
import { useAdminUsers } from '@/features/admin/hooks/use-admin-users'
import { useCurrentUser } from '@/features/auth/hooks/use-auth'
import { ProjectFormDialog } from '@/features/projects/components/ProjectFormDialog'
import {
  useProject,
  useProjectMembers,
  useProjectMutations,
} from '@/features/projects/hooks/use-projects'
import type { ProjectMembershipRole } from '@/features/account/types'
import { toast } from '@/lib/toast'
import { getApiErrorMessage } from '@/lib/errors'

export function ProjectDetailPage() {
  const { projectId = '' } = useParams()
  const navigate = useNavigate()
  const { data: me } = useCurrentUser()
  const isAdmin = me?.role === 'admin'

  const { data: project, isLoading, isError, error } = useProject(projectId)
  const { data: members = [] } = useProjectMembers(projectId)
  const { data: users = [] } = useAdminUsers(isAdmin)
  const mutations = useProjectMutations()

  const [editOpen, setEditOpen] = useState(false)
  const [memberUserId, setMemberUserId] = useState('')
  const [memberRole, setMemberRole] =
    useState<ProjectMembershipRole>('member')

  const userById = useMemo(
    () => Object.fromEntries(users.map((u) => [u.id, u])),
    [users],
  )

  const availableUsers = users.filter(
    (u) => !members.some((m) => m.user_id === u.id),
  )

  if (!isAdmin) {
    return (
      <EmptyState
        title="Admin only"
        description="Project management is limited to admins and project owners via the API. Use Directories to browse."
        action={
          <Button asChild variant="outline" size="sm">
            <Link to="/projects">Back to projects</Link>
          </Button>
        }
      />
    )
  }

  if (isLoading) {
    return <LoadingState label="Loading project…" />
  }

  if (isError || !project) {
    return (
      <p className="text-destructive">
        Could not load project: {(error as Error)?.message ?? 'Not found'}
      </p>
    )
  }

  return (
    <section className="animate-fade-up space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-sm text-muted-foreground">
            <Link to="/projects" className="hover:underline">
              Projects
            </Link>
            <span className="mx-1.5">/</span>
            {project.name}
          </p>
          <h1 className="font-heading mt-1 text-3xl tracking-tight">
            {project.name}
          </h1>
          {project.description ? (
            <p className="mt-1 text-muted-foreground">{project.description}</p>
          ) : null}
          {project.is_archived ? (
            <p className="mt-1 text-xs text-muted-foreground">Archived</p>
          ) : null}
        </div>
        <div className="flex flex-wrap gap-2">
          <Button asChild variant="outline" size="sm">
            <Link to={`/projects/${project.id}/directories`}>Directories</Link>
          </Button>
          <Button size="sm" variant="outline" onClick={() => setEditOpen(true)}>
            Edit
          </Button>
          {project.is_archived ? (
            <Button
              size="sm"
              variant="outline"
              disabled={mutations.unarchive.isPending}
              onClick={() =>
                mutations.unarchive.mutate(project.id, {
                  onSuccess: () => toast.success('Project restored'),
                  onError: (err) =>
                    toast.error(getApiErrorMessage(err)),
                })
              }
            >
              Unarchive
            </Button>
          ) : (
            <Button
              size="sm"
              variant="outline"
              disabled={mutations.archive.isPending}
              onClick={() =>
                mutations.archive.mutate(project.id, {
                  onSuccess: () => toast.success('Project archived'),
                  onError: (err) =>
                    toast.error(getApiErrorMessage(err)),
                })
              }
            >
              Archive
            </Button>
          )}
          <Button
            size="sm"
            variant="destructive"
            disabled={mutations.remove.isPending}
            onClick={() => {
              if (
                !window.confirm(
                  `Delete project “${project.name}”? This cannot be undone.`,
                )
              ) {
                return
              }
              mutations.remove.mutate(project.id, {
                onSuccess: () => {
                  toast.success('Project deleted')
                  navigate('/projects')
                },
                onError: (err) =>
                  toast.error(getApiErrorMessage(err, 'Delete failed')),
              })
            }}
          >
            Delete
          </Button>
        </div>
      </div>

      <Separator />

      <div className="space-y-4">
        <h2 className="font-heading text-xl">Members</h2>
        <ul className="divide-y divide-border border-y border-border">
          {members.map((member) => {
            const user = userById[member.user_id]
            return (
              <li
                key={member.id}
                className="flex flex-wrap items-center justify-between gap-3 py-3"
              >
                <div>
                  <p className="font-medium">
                    {user?.email ?? member.user_id}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {member.role}
                    {user?.full_name ? ` · ${user.full_name}` : ''}
                  </p>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={mutations.removeMember.isPending}
                  onClick={() =>
                    mutations.removeMember.mutate(
                      { projectId: project.id, userId: member.user_id },
                      {
                        onSuccess: () => toast.success('Member removed'),
                        onError: (err) =>
                          toast.error(getApiErrorMessage(err, 'Remove failed')),
                      },
                    )
                  }
                >
                  Remove
                </Button>
              </li>
            )
          })}
          {members.length === 0 ? (
            <li className="py-3 text-sm text-muted-foreground">
              No members yet.
            </li>
          ) : null}
        </ul>

        <div className="flex flex-wrap items-end gap-2">
          {availableUsers.length > 0 ? (
            <Select value={memberUserId} onValueChange={setMemberUserId}>
              <SelectTrigger className="w-[16rem]">
                <SelectValue placeholder="Select user" />
              </SelectTrigger>
              <SelectContent>
                {availableUsers.map((u) => (
                  <SelectItem key={u.id} value={u.id}>
                    {u.email}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ) : (
            <Input
              className="max-w-xs"
              placeholder="User UUID"
              value={memberUserId}
              onChange={(e) => setMemberUserId(e.target.value)}
            />
          )}
          <Select
            value={memberRole}
            onValueChange={(v) => setMemberRole(v as ProjectMembershipRole)}
          >
            <SelectTrigger className="w-[8rem]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="member">member</SelectItem>
              <SelectItem value="owner">owner</SelectItem>
            </SelectContent>
          </Select>
          <Button
            size="sm"
            disabled={!memberUserId || mutations.addMember.isPending}
            onClick={() =>
              mutations.addMember.mutate(
                {
                  projectId: project.id,
                  userId: memberUserId,
                  role: memberRole,
                },
                {
                  onSuccess: () => {
                    toast.success('Member added')
                    setMemberUserId('')
                  },
                  onError: (err) =>
                    toast.error(getApiErrorMessage(err, 'Add failed')),
                },
              )
            }
          >
            Add member
          </Button>
        </div>
      </div>

      <ProjectFormDialog
        open={editOpen}
        onOpenChange={setEditOpen}
        title="Edit project"
        description="Update name or description."
        confirmLabel="Save"
        pending={mutations.update.isPending}
        initial={{
          name: project.name,
          description: project.description,
        }}
        onSubmit={(values) => {
          mutations.update.mutate(
            {
              projectId: project.id,
              body: {
                name: values.name,
                description: values.description || null,
              },
            },
            {
              onSuccess: () => {
                toast.success('Project updated')
                setEditOpen(false)
              },
              onError: (err) =>
                toast.error(getApiErrorMessage(err, 'Update failed')),
            },
          )
        }}
      />
    </section>
  )
}
