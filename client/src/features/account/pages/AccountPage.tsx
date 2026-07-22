import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { EmptyState } from '@/components/EmptyState'
import { LoadingState } from '@/components/LoadingState'
import {
  useAccountMutations,
  useAccountProjects,
} from '@/features/account/hooks/use-account'
import { toast } from '@/lib/toast'
import { getApiErrorMessage } from '@/lib/errors'

export function AccountPage() {
  const { data: projects = [], isLoading, isError, error } =
    useAccountProjects()
  const { setContextExposed } = useAccountMutations()

  if (isLoading) {
    return <LoadingState label="Loading account…" />
  }

  if (isError) {
    return (
      <p className="text-destructive">
        Could not load account: {(error as Error).message}
      </p>
    )
  }

  return (
    <section className="animate-fade-up space-y-6">
      <div>
        <h1 className="font-heading text-3xl tracking-tight">Account</h1>
        <p className="mt-1 max-w-prose text-muted-foreground">
          Projects you belong to. Toggle{' '}
          <span className="font-medium text-foreground">MCP exposure</span> so
          coding agents can receive that project’s ProjectContext via{' '}
          <code className="text-xs">get_project_context</code>.
        </p>
      </div>

      {projects.length === 0 ? (
        <EmptyState
          title="No memberships yet"
          description="Ask an admin to add you to a project."
          action={
            <Button asChild variant="outline" size="sm">
              <Link to="/projects">Browse projects</Link>
            </Button>
          }
        />
      ) : (
        <ul className="divide-y divide-border border-y border-border">
          {projects.map((project) => (
            <li
              key={project.id}
              className="flex flex-wrap items-center justify-between gap-4 py-4"
            >
              <div>
                <p className="font-medium">{project.name}</p>
                <p className="text-sm text-muted-foreground">
                  Role: {project.membership_role}
                  {project.is_archived ? ' · Archived' : ''}
                </p>
              </div>
              <label className="flex cursor-pointer items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  className="size-4 accent-[oklch(0.45_0.08_65)]"
                  checked={project.is_context_exposed}
                  disabled={setContextExposed.isPending}
                  onChange={(e) => {
                    // Capture before mutate: onSuccess runs after re-render, and
                    // the controlled checkbox can flip e.target.checked from stale cache.
                    const exposed = e.target.checked
                    setContextExposed.mutate(
                      {
                        projectId: project.id,
                        is_context_exposed: exposed,
                      },
                      {
                        onSuccess: () =>
                          toast.success(
                            exposed
                              ? 'Project exposed to MCP'
                              : 'Project hidden from MCP',
                          ),
                        onError: (err) =>
                          toast.error(getApiErrorMessage(err, 'Could not update')),
                      },
                    )
                  }}
                />
                Expose to MCP
              </label>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
