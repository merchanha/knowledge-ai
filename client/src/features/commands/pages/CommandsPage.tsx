import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import {
  BrowseContextBar,
  ProjectFolderSidebar,
  ProjectPicker,
} from '@/components/browse/ProjectFolderBrowser'
import { CommandPanel } from '@/features/commands/components/CommandPanel'
import { useDirectoryTree } from '@/features/directories/hooks/use-directory-tree'
import { useProject, useProjects } from '@/features/projects/hooks/use-projects'

const BASE = '/commands'

/**
 * Same browse shell as KnowledgeNeurons — intentionally parallel, no search.
 */
export function CommandsPage() {
  const { projectId = '', directoryId } = useParams()
  const navigate = useNavigate()
  const [filter, setFilter] = useState('')

  const { data: projects = [], isLoading: projectsLoading } = useProjects()
  const { data: project } = useProject(projectId || undefined)
  const { tree, flat, isLoading: treeLoading } = useDirectoryTree(
    projectId || undefined,
  )

  const rootId = flat.find((d) => d.is_root)?.id ?? flat[0]?.id
  const selected = directoryId ?? rootId
  const folderName = flat.find((d) => d.id === selected)?.name

  useEffect(() => {
    if (!projectId || directoryId || !rootId || treeLoading) return
    navigate(`${BASE}/projects/${projectId}/directories/${rootId}`, {
      replace: true,
    })
  }, [projectId, directoryId, rootId, treeLoading, navigate])

  return (
    <section className="animate-fade-up flex min-h-0 flex-1 flex-col gap-5">
      <div>
        <h1 className="font-heading text-3xl tracking-tight">Commands</h1>
        <p className="mt-1 max-w-prose text-muted-foreground">
          Instruction snippets scoped to folders — pick a project, open a
          folder, then create or edit Commands (no embeddings or semantic
          search).
        </p>
      </div>

      <div className="grid min-h-[28rem] flex-1 gap-5 lg:grid-cols-[minmax(15rem,18rem)_1fr]">
        <ProjectFolderSidebar
          projects={projects}
          selectedProjectId={projectId || undefined}
          selectedDirectoryId={selected}
          tree={tree}
          treeLoading={treeLoading}
          basePath={BASE}
          emptyHint={
            projectsLoading
              ? 'Loading projects…'
              : 'No projects yet. Create one under Projects.'
          }
        />

        <div className="min-w-0 space-y-4">
          {!projectId ? (
            <ProjectPicker
              projects={projects}
              basePath={BASE}
              title="Pick a project"
              description="Choose a project, then a folder in the sidebar, to browse and create Commands."
            />
          ) : (
            <>
              <BrowseContextBar
                projectName={project?.name}
                folderName={folderName}
                filter={filter}
                onFilterChange={setFilter}
                filterPlaceholder="Filter commands…"
              />
              {selected ? (
                <CommandPanel
                  directoryId={selected}
                  canWrite
                  canManage
                  filter={filter}
                />
              ) : (
                <p className="text-sm text-muted-foreground">
                  {treeLoading
                    ? 'Loading folders…'
                    : 'This project has no folders yet.'}
                </p>
              )}
            </>
          )}
        </div>
      </div>
    </section>
  )
}
