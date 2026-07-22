import { MoreHorizontal } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useState } from 'react'

import { CreateItemCard, ItemCard, StatusChip } from '@/components/ItemCard'
import { EmptyState } from '@/components/EmptyState'
import { LoadingState } from '@/components/LoadingState'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useCurrentUser } from '@/features/auth/hooks/use-auth'
import { ProjectFormDialog } from '@/features/projects/components/ProjectFormDialog'
import {
  useProjectMutations,
  useProjects,
} from '@/features/projects/hooks/use-projects'
import { getApiErrorMessage } from '@/lib/errors'
import { toast } from '@/lib/toast'

export function ProjectsPage() {
  const { data: me } = useCurrentUser()
  const isAdmin = me?.role === 'admin'
  const { data: projects = [], isLoading, isError, error } = useProjects()
  const mutations = useProjectMutations()
  const [createOpen, setCreateOpen] = useState(false)

  if (isLoading) {
    return <LoadingState label="Loading projects…" />
  }

  if (isError) {
    return (
      <p className="text-destructive">
        Could not load projects: {getApiErrorMessage(error)}
      </p>
    )
  }

  return (
    <section className="animate-fade-up space-y-6">
      <div>
        <h1 className="font-heading text-3xl tracking-tight">Projects</h1>
        <p className="mt-1 text-muted-foreground">
          Open a project workspace to browse folders, KnowledgeNeurons, and
          Commands.
        </p>
      </div>

      {projects.length === 0 && !isAdmin ? (
        <EmptyState
          title="No projects yet"
          description="Ask an admin to create one and add you as a member."
        />
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {projects.map((project, index) => (
            <div
              key={project.id}
              className="animate-card-in"
              style={{ animationDelay: `${Math.min(index, 8) * 40}ms` }}
            >
              <ItemCard
                typeLabel="Project"
                title={project.name}
                body={project.description ?? undefined}
                accent="project"
                chips={
                  project.is_archived ? (
                    <StatusChip tone="pending">Archived</StatusChip>
                  ) : (
                    <StatusChip tone="success">Active</StatusChip>
                  )
                }
                menu={
                  isAdmin ? (
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          aria-label={`Actions for ${project.name}`}
                        >
                          <MoreHorizontal className="size-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem asChild>
                          <Link to={`/projects/${project.id}`}>Manage</Link>
                        </DropdownMenuItem>
                        <DropdownMenuItem asChild>
                          <Link to={`/projects/${project.id}/directories`}>
                            Open workspace
                          </Link>
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  ) : null
                }
              >
                <div className="mt-4">
                  <Button asChild size="sm" className="w-full sm:w-auto">
                    <Link to={`/projects/${project.id}/directories`}>
                      Open workspace
                    </Link>
                  </Button>
                </div>
              </ItemCard>
            </div>
          ))}
          {isAdmin ? (
            <CreateItemCard
              label="New project"
              onClick={() => setCreateOpen(true)}
            />
          ) : null}
        </div>
      )}

      <ProjectFormDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        title="New project"
        description="Creates a root directory and is ready for members."
        confirmLabel="Create"
        pending={mutations.create.isPending}
        onSubmit={(values) => {
          mutations.create.mutate(
            {
              name: values.name,
              description: values.description || null,
            },
            {
              onSuccess: () => {
                toast.success('Project created')
                setCreateOpen(false)
              },
              onError: (err) =>
                toast.error(getApiErrorMessage(err, 'Create failed')),
            },
          )
        }}
      />
    </section>
  )
}
