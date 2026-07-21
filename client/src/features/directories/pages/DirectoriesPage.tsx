import { useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { useCurrentUser } from '@/features/auth/hooks/use-auth'
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
import { useProject } from '@/features/projects/hooks/use-projects'

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
  // Weeks 15–17: treat members with tree access as able to write; fine-grained
  // per-node Casbin UI lands with later admin polish. Admins always can.
  const canWrite = true
  const canManage = isAdmin

  const moveTargets = useMemo(() => {
    if (dialog.type !== 'move') return []
    return listMoveTargets(flat, dialog.node.id)
  }, [dialog, flat])

  const selected =
    directoryId ??
    flat.find((d) => d.is_root)?.id ??
    flat[0]?.id

  const closeDialog = () => setDialog({ type: 'idle' })

  if (isLoading) {
    return <p className="text-muted-foreground">Loading directory tree…</p>
  }

  if (isError) {
    return (
      <p className="text-destructive">
        Could not load directories: {(error as Error).message}
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
            Directories
          </h1>
        </div>
        {selected ? (
          <DirectoryBreadcrumbs
            projectId={projectId}
            directoryId={selected}
          />
        ) : null}
      </div>

      <Separator />

      <div className="grid min-h-[28rem] flex-1 gap-6 lg:grid-cols-[minmax(16rem,20rem)_1fr]">
        <aside className="rounded-lg border border-border/80 bg-[oklch(0.99_0.004_85_/_0.7)] p-2">
          <ScrollArea className="h-[28rem] pr-2">
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
        </aside>

        <div className="space-y-3">
          <h2 className="font-heading text-xl">
            {flat.find((d) => d.id === selected)?.name ?? 'Select a folder'}
          </h2>
          <p className="max-w-prose text-sm text-muted-foreground">
            KnowledgeNeuron and Command lists for this folder arrive in Weeks
            18–19. For now, navigate the tree, rename/move folders, and (as
            admin) manage directory permissions.
          </p>
          {selected && canWrite ? (
            <Button
              size="sm"
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
