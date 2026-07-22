import { ChevronRight, FolderOpen, LayoutGrid } from 'lucide-react'
import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { DirectoryTree } from '@/features/directories/components/DirectoryTree'
import type { DirectoryTreeNode } from '@/features/directories/types'
import type { Project } from '@/features/projects/types'
import { cn } from '@/lib/utils'

interface ProjectFolderSidebarProps {
  projects: Project[]
  selectedProjectId?: string
  selectedDirectoryId?: string
  tree: DirectoryTreeNode[]
  treeLoading?: boolean
  /** Base path before /projects/:id — e.g. `/knowledge` or `/commands` */
  basePath: string
  emptyHint?: string
}

export function ProjectFolderSidebar({
  projects,
  selectedProjectId,
  selectedDirectoryId,
  tree,
  treeLoading,
  basePath,
  emptyHint = 'No projects yet.',
}: ProjectFolderSidebarProps) {
  return (
    <aside className="lg:sticky lg:top-4 lg:self-start">
      <div className="rounded-lg border border-border/80 bg-[oklch(0.99_0.004_85_/_0.9)] shadow-sm">
        <div className="flex items-center justify-between border-b border-border/70 px-3 py-2.5">
          <p className="text-[0.65rem] font-semibold tracking-[0.12em] text-muted-foreground uppercase">
            Workspace
          </p>
          <Button asChild variant="ghost" size="sm" className="h-7 px-2 text-xs">
            <Link to="/projects">All projects</Link>
          </Button>
        </div>

        {projects.length === 0 ? (
          <p className="px-3 py-4 text-sm text-muted-foreground">{emptyHint}</p>
        ) : (
          <ScrollArea className="h-[min(32rem,70vh)]">
            <ul className="space-y-1 p-2">
              {projects.map((project) => {
                const active = project.id === selectedProjectId
                return (
                  <li key={project.id}>
                    <Link
                      to={`${basePath}/projects/${project.id}`}
                      className={cn(
                        'flex items-center gap-2 rounded-md px-2 py-2 text-sm transition-colors',
                        active
                          ? 'bg-sidebar-accent font-medium text-sidebar-accent-foreground'
                          : 'text-muted-foreground hover:bg-muted/70 hover:text-foreground',
                      )}
                    >
                      <ChevronRight
                        className={cn(
                          'size-3.5 shrink-0 transition-transform',
                          active && 'rotate-90',
                        )}
                      />
                      <LayoutGrid className="size-3.5 shrink-0 text-[oklch(0.55_0.08_65)]" />
                      <span className="truncate">{project.name}</span>
                    </Link>

                    {active ? (
                      <div className="mt-1 mb-2 ml-2 rounded-md border border-border/60 bg-[oklch(0.985_0.004_85)] p-1.5">
                        {treeLoading ? (
                          <p className="px-2 py-3 text-xs text-muted-foreground">
                            Loading folders…
                          </p>
                        ) : tree.length === 0 ? (
                          <p className="px-2 py-3 text-xs text-muted-foreground">
                            No folders in this project.
                          </p>
                        ) : (
                          <DirectoryTree
                            projectId={project.id}
                            tree={tree}
                            selectedId={selectedDirectoryId}
                            canWrite={false}
                            canManage={false}
                            isAdmin={false}
                            basePath={`${basePath}/projects/${project.id}/directories`}
                            actions={{
                              onCreateChild: () => undefined,
                              onRename: () => undefined,
                              onMove: () => undefined,
                              onDelete: () => undefined,
                            }}
                          />
                        )}
                      </div>
                    ) : null}
                  </li>
                )
              })}
            </ul>
          </ScrollArea>
        )}
      </div>
    </aside>
  )
}

interface BrowseContextBarProps {
  projectName?: string
  folderName?: string
  filter?: string
  onFilterChange?: (value: string) => void
  filterPlaceholder?: string
}

export function BrowseContextBar({
  projectName,
  folderName,
  filter,
  onFilterChange,
  filterPlaceholder = 'Filter…',
}: BrowseContextBarProps) {
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-lg border border-border/70 bg-[oklch(0.99_0.004_85_/_0.75)] px-3 py-2.5">
      <div className="flex min-w-0 flex-wrap items-center gap-2 text-xs">
        <span className="inline-flex items-center gap-1.5 rounded-md bg-muted/80 px-2 py-1 text-muted-foreground">
          <span className="font-semibold tracking-wide uppercase">Project</span>
          <span className="max-w-[10rem] truncate font-medium text-foreground">
            {projectName ?? '—'}
          </span>
        </span>
        <span className="inline-flex items-center gap-1.5 rounded-md bg-muted/80 px-2 py-1 text-muted-foreground">
          <FolderOpen className="size-3.5 text-[oklch(0.55_0.08_65)]" />
          <span className="font-semibold tracking-wide uppercase">Folder</span>
          <span className="max-w-[10rem] truncate font-medium text-foreground">
            {folderName ?? '—'}
          </span>
        </span>
      </div>
      {onFilterChange ? (
        <input
          value={filter ?? ''}
          onChange={(e) => onFilterChange(e.target.value)}
          placeholder={filterPlaceholder}
          aria-label={filterPlaceholder}
          className="border-input bg-background placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-ring/50 ml-auto h-8 min-w-[12rem] flex-1 rounded-md border px-3 text-sm outline-none focus-visible:ring-[3px] sm:max-w-xs"
        />
      ) : null}
    </div>
  )
}

interface ProjectPickerProps {
  projects: Project[]
  basePath: string
  title: string
  description: string
}

export function ProjectPicker({
  projects,
  basePath,
  title,
  description,
}: ProjectPickerProps) {
  return (
    <div className="animate-fade-up flex flex-col items-stretch justify-center rounded-lg border border-dashed border-border/80 bg-[oklch(0.99_0.004_85_/_0.55)] px-6 py-10">
      <div className="mx-auto max-w-lg text-center">
        <p className="font-heading text-2xl tracking-tight">{title}</p>
        <p className="mt-2 text-sm text-muted-foreground">{description}</p>
      </div>

      {projects.length === 0 ? (
        <div className="mx-auto mt-8 text-center">
          <p className="text-sm text-muted-foreground">
            You don’t have any projects yet.
          </p>
          <Button asChild className="mt-4" size="sm">
            <Link to="/projects">Go to Projects</Link>
          </Button>
        </div>
      ) : (
        <ul className="mx-auto mt-8 grid w-full max-w-2xl gap-3 sm:grid-cols-2">
          {projects.map((project, index) => (
            <li
              key={project.id}
              className="animate-card-in"
              style={{ animationDelay: `${Math.min(index, 6) * 40}ms` }}
            >
              <Link
                to={`${basePath}/projects/${project.id}`}
                className={cn(
                  'flex h-full flex-col rounded-lg border border-border/80 bg-[oklch(0.995_0.003_85)] p-4 text-left shadow-sm transition-[transform,box-shadow,border-color]',
                  'hover:-translate-y-0.5 hover:border-[oklch(0.75_0.06_65_/_0.55)] hover:shadow-md',
                )}
              >
                <p className="text-[0.65rem] font-semibold tracking-[0.14em] text-muted-foreground uppercase">
                  Project
                </p>
                <p className="font-heading mt-1 text-lg tracking-tight">
                  {project.name}
                </p>
                {project.description ? (
                  <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">
                    {project.description}
                  </p>
                ) : (
                  <p className="mt-1 text-sm text-muted-foreground">
                    Open folders to manage items
                  </p>
                )}
                <span className="mt-4 text-sm font-medium text-[oklch(0.4_0.06_65)]">
                  Browse folders →
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
