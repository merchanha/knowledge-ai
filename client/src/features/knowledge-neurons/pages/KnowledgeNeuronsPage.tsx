import { useEffect, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'

import {
  BrowseContextBar,
  ProjectFolderSidebar,
  ProjectPicker,
} from '@/components/browse/ProjectFolderBrowser'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useDirectoryTree } from '@/features/directories/hooks/use-directory-tree'
import { KnowledgeNeuronList } from '@/features/knowledge-neurons/components/KnowledgeNeuronList'
import { KnowledgeNeuronPanel } from '@/features/knowledge-neurons/components/KnowledgeNeuronPanel'
import { useKnowledgeNeuronSearch } from '@/features/knowledge-neurons/hooks/use-knowledge-neurons'
import { useProject, useProjects } from '@/features/projects/hooks/use-projects'
import { getApiErrorMessage } from '@/lib/errors'

const BASE = '/knowledge'

export function KnowledgeNeuronsPage() {
  const { projectId = '', directoryId } = useParams()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const q = searchParams.get('q') ?? ''
  const [draft, setDraft] = useState(q)
  const [filter, setFilter] = useState('')

  const { data: projects = [], isLoading: projectsLoading } = useProjects()
  const { data: project } = useProject(projectId || undefined)
  const { tree, flat, isLoading: treeLoading } = useDirectoryTree(
    projectId || undefined,
  )
  const search = useKnowledgeNeuronSearch(q || undefined)

  const rootId = flat.find((d) => d.is_root)?.id ?? flat[0]?.id
  const selected = directoryId ?? rootId
  const folderName = flat.find((d) => d.id === selected)?.name

  // Land on the root folder once the tree loads so the main pane isn't empty.
  useEffect(() => {
    if (!projectId || directoryId || !rootId || treeLoading) return
    navigate(`${BASE}/projects/${projectId}/directories/${rootId}`, {
      replace: true,
    })
  }, [projectId, directoryId, rootId, treeLoading, navigate])

  const applySearch = (term: string) => {
    const trimmed = term.trim()
    if (trimmed) {
      setSearchParams({ q: trimmed })
    } else {
      setSearchParams({})
    }
  }

  const searching = q.trim().length > 0

  return (
    <section className="animate-fade-up flex min-h-0 flex-1 flex-col gap-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-heading text-3xl tracking-tight">
            KnowledgeNeurons
          </h1>
          <p className="mt-1 max-w-prose text-muted-foreground">
            Stored knowledge in project folders — browse a folder or search
            semantically across everything you can read.
          </p>
        </div>
      </div>

      <form
        className="flex flex-wrap gap-2"
        onSubmit={(e) => {
          e.preventDefault()
          applySearch(draft)
        }}
      >
        <Input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Semantic search across readable folders…"
          className="max-w-md"
          aria-label="Search KnowledgeNeurons"
        />
        <Button type="submit" size="sm">
          Search
        </Button>
        {searching ? (
          <Button
            type="button"
            size="sm"
            variant="ghost"
            onClick={() => {
              setDraft('')
              applySearch('')
            }}
          >
            Clear search
          </Button>
        ) : null}
      </form>

      {searching ? (
        <div className="space-y-4">
          <BrowseContextBar projectName="All readable folders" folderName="Search" />
          <h2 className="font-heading text-xl">Results for “{q.trim()}”</h2>
          {search.isLoading ? (
            <p className="text-sm text-muted-foreground">Searching…</p>
          ) : search.isError ? (
            <p className="text-sm text-destructive">
              Search failed: {getApiErrorMessage(search.error)}
            </p>
          ) : (
            <KnowledgeNeuronList
              neurons={(search.data ?? []).map((row) => ({
                id: row.id,
                directory_id: row.directory_id,
                title: row.title,
                content: row.content,
                metadata: row.metadata,
                has_embedding: true,
              }))}
              emptyMessage="No strong matches. Try a natural-language question (semantic search), or wait for new neurons to embed."
              similarityById={Object.fromEntries(
                (search.data ?? []).map((row) => [row.id, row.similarity]),
              )}
            />
          )}
        </div>
      ) : (
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
                description="Choose a project, then a folder in the sidebar, to browse and create KnowledgeNeurons."
              />
            ) : (
              <>
                <BrowseContextBar
                  projectName={project?.name}
                  folderName={folderName}
                  filter={filter}
                  onFilterChange={setFilter}
                  filterPlaceholder="Filter KnowledgeNeurons…"
                />
                {selected ? (
                  <KnowledgeNeuronPanel
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
      )}
    </section>
  )
}
