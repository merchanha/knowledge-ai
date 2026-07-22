import { useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { LoadingState } from '@/components/LoadingState'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useCurrentUser } from '@/features/auth/hooks/use-auth'
import { CommandPanel } from '@/features/commands/components/CommandPanel'
import { DeleteDirectoryDialog } from '@/features/directories/components/DeleteDirectoryDialog'
import { DirectoryBreadcrumbs } from '@/features/directories/components/DirectoryBreadcrumbs'
import { DirectoryTree } from '@/features/directories/components/DirectoryTree'
import { MoveDirectoryDialog } from '@/features/directories/components/MoveDirectoryDialog'
import { NameDirectoryDialog } from '@/features/directories/components/NameDirectoryDialog'
import { PermissionDialog } from '@/features/directories/components/PermissionDialog'
import {
  useDirectoryMutations,
  useDirectoryTree,
} from '@/features/directories/hooks/use-directory-tree'
import type { DirectoryTreeNode } from '@/features/directories/types'
import { listMoveTargets } from '@/features/directories/utils/tree'
import { KnowledgeNeuronPanel } from '@/features/knowledge-neurons/components/KnowledgeNeuronPanel'
import { useProject } from '@/features/projects/hooks/use-projects'
import { getApiErrorMessage } from '@/lib/errors'

type DialogState =
  | { type: 'idle' }
  | { type: 'create'; parent: DirectoryTreeNode }
  | { type: 'rename'; node: DirectoryTreeNode }
  | { type: 'move'; node: DirectoryTreeNode }
  | { type: 'delete'; node: DirectoryTreeNode }
  | { type: 'permissions'; node: DirectoryTreeNode }

export function DirectoriesPage() {
  const { projectId = '', directoryId } = useParams()
  const navigate = useNavigate()
  const { data: me } = useCurrentUser()
  const { data: project } = useProject(projectId)
  const { tree, flat, isLoading, isError, error } = useDirectoryTree(projectId)
  const mutations = useDirectoryMutations(projectId)
  const [dialog, setDialog] = useState<DialogState>({ type: 'idle' })

  const isAdmin = me?.role === 'admin'
  const canWrite = true
  const canManage = isAdmin

  const moveTargets = useMemo(() => {
    if (dialog.type !== 'move') return []
    return listMoveTargets(flat, dialog.node.id)
  }, [dialog, flat])

  const selected =
    directoryId ?? flat.find((d) => d.is_root)?.id ?? flat[0]?.id

  const selectedName =
    flat.find((d) => d.id === selected)?.name ?? 'Select a folder'

  const closeDialog = () => setDialog({ type: 'idle' })

  if (isLoading) {
    return <LoadingState label="Loading directory tree…" />
  }

  if (isError) {
    return (
      <p className="text-destructive">
        Could not load directories: {getApiErrorMessage(error)}
      </p>
    )
  }

  return (
    <section className="animate-fade-up flex min-h-0 flex-1 flex-col gap-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-sm text-muted-foreground">
            <Link to="/projects" className="hover:underline">
              Projects
            </Link>
            <span className="mx-1.5">/</span>
            {project?.name ?? '…'}
          </p>
          <h1 className="font-heading mt-1 text-3xl tracking-tight">
            Workspace
          </h1>
        </div>
      </div>

      <div className="grid min-h-0 flex-1 gap-4 lg:grid-cols-[minmax(15rem,18rem)_1fr]">
        <aside className="lg:sticky lg:top-4 lg:self-start">
          <div className="rounded-lg border border-border/80 bg-[oklch(0.99_0.004_85_/_0.85)] p-2 shadow-sm">
            <p className="px-2 py-1.5 text-[0.65rem] font-semibold tracking-[0.12em] text-muted-foreground uppercase">
              Folders
            </p>
            <ScrollArea className="h-[min(28rem,60vh)] pr-2 lg:h-[min(36rem,70vh)]">
              <DirectoryTree
                projectId={projectId}
                tree={tree}
                selectedId={selected}
                canWrite={canWrite}
                canManage={canManage}
                isAdmin={isAdmin}
                actions={{
                  onCreateChild: (parent) =>
                    setDialog({ type: 'create', parent }),
                  onRename: (node) => setDialog({ type: 'rename', node }),
                  onMove: (node) => setDialog({ type: 'move', node }),
                  onDelete: (node) => setDialog({ type: 'delete', node }),
                  onManagePermissions: isAdmin
                    ? (node) => setDialog({ type: 'permissions', node })
                    : undefined,
                }}
              />
            </ScrollArea>
          </div>
        </aside>

        <div className="min-w-0 space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-border/70 bg-[oklch(0.99_0.004_85_/_0.7)] px-4 py-3">
            <div className="min-w-0 space-y-1">
              <h2 className="font-heading truncate text-xl">{selectedName}</h2>
              {selected ? (
                <DirectoryBreadcrumbs
                  projectId={projectId}
                  directoryId={selected}
                />
              ) : null}
            </div>
            {selected && canWrite ? (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  const parent = flat.find((d) => d.id === selected)
                  if (!parent) return
                  setDialog({
                    type: 'create',
                    parent: { ...parent, children: [] },
                  })
                }}
              >
                New child folder
              </Button>
            ) : null}
          </div>

          <KnowledgeNeuronPanel
            directoryId={selected}
            canWrite={canWrite}
            canManage={canManage || isAdmin}
          />

          <CommandPanel
            directoryId={selected}
            canWrite={canWrite}
            canManage={canManage || isAdmin}
          />
        </div>
      </div>

      <NameDirectoryDialog
        open={dialog.type === 'create'}
        onOpenChange={(open) => !open && closeDialog()}
        title="New folder"
        description={
          dialog.type === 'create'
            ? `Create a child under “${dialog.parent.name}”.`
            : ''
        }
        confirmLabel="Create"
        pending={mutations.createChild.isPending}
        onSubmit={(name) => {
          if (dialog.type !== 'create') return
          mutations.createChild.mutate(
            { parentId: dialog.parent.id, name },
            {
              onSuccess: (created) => {
                closeDialog()
                navigate(
                  `/projects/${projectId}/directories/${created.id}`,
                )
              },
            },
          )
        }}
      />

      <NameDirectoryDialog
        open={dialog.type === 'rename'}
        onOpenChange={(open) => !open && closeDialog()}
        title="Rename folder"
        description="Sibling names must stay unique under the same parent."
        initialName={dialog.type === 'rename' ? dialog.node.name : ''}
        confirmLabel="Save"
        pending={mutations.rename.isPending}
        onSubmit={(name) => {
          if (dialog.type !== 'rename') return
          mutations.rename.mutate(
            { directoryId: dialog.node.id, name },
            { onSuccess: () => closeDialog() },
          )
        }}
      />

      <MoveDirectoryDialog
        open={dialog.type === 'move'}
        onOpenChange={(open) => !open && closeDialog()}
        directoryName={dialog.type === 'move' ? dialog.node.name : ''}
        targets={moveTargets}
        pending={mutations.move.isPending}
        onSubmit={(newParentId) => {
          if (dialog.type !== 'move') return
          mutations.move.mutate(
            { directoryId: dialog.node.id, newParentId },
            { onSuccess: () => closeDialog() },
          )
        }}
      />

      <DeleteDirectoryDialog
        open={dialog.type === 'delete'}
        onOpenChange={(open) => !open && closeDialog()}
        directoryName={dialog.type === 'delete' ? dialog.node.name : ''}
        pending={mutations.remove.isPending}
        onConfirm={() => {
          if (dialog.type !== 'delete') return
          const deletedId = dialog.node.id
          mutations.remove.mutate(deletedId, {
            onSuccess: () => {
              closeDialog()
              if (directoryId === deletedId) {
                const root = flat.find((d) => d.is_root)
                navigate(
                  root
                    ? `/projects/${projectId}/directories/${root.id}`
                    : `/projects/${projectId}/directories`,
                )
              }
            },
          })
        }}
      />

      <PermissionDialog
        open={dialog.type === 'permissions'}
        onOpenChange={(open) => !open && closeDialog()}
        directoryName={
          dialog.type === 'permissions' ? dialog.node.name : ''
        }
        pending={
          mutations.grantPermission.isPending ||
          mutations.revokePermission.isPending
        }
        onGrant={(userId, permission) => {
          if (dialog.type !== 'permissions') return
          mutations.grantPermission.mutate({
            directoryId: dialog.node.id,
            userId,
            permission,
          })
        }}
        onRevoke={(userId, permission) => {
          if (dialog.type !== 'permissions') return
          mutations.revokePermission.mutate({
            directoryId: dialog.node.id,
            userId,
            permission,
          })
        }}
      />
    </section>
  )
}
