import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { useProjects } from '@/features/projects/hooks/use-projects'

export function ProjectsPage() {
  const { data: projects = [], isLoading, isError, error } = useProjects()

  if (isLoading) {
    return <p className="text-muted-foreground">Loading projects…</p>
  }

  if (isError) {
    return (
      <p className="text-destructive">
        Could not load projects: {(error as Error).message}
      </p>
    )
  }

  return (
    <section className="animate-fade-up space-y-6">
      <div>
        <h1 className="font-heading text-3xl tracking-tight">Projects</h1>
        <p className="mt-1 text-muted-foreground">
          Pick a project to browse its directory tree.
        </p>
      </div>

      {projects.length === 0 ? (
        <p className="text-muted-foreground">
          No projects yet. Ask an admin to create one and add you as a member.
        </p>
      ) : (
        <ul className="divide-y divide-border border-y border-border">
          {projects.map((project) => (
            <li
              key={project.id}
              className="flex flex-wrap items-center justify-between gap-3 py-4"
            >
              <div>
                <p className="font-medium">{project.name}</p>
                {project.description ? (
                  <p className="text-sm text-muted-foreground">
                    {project.description}
                  </p>
                ) : null}
                {project.is_archived ? (
                  <p className="text-xs text-muted-foreground">Archived</p>
                ) : null}
              </div>
              <Button asChild variant="outline" size="sm">
                <Link to={`/projects/${project.id}/directories`}>
                  Open directories
                </Link>
              </Button>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
