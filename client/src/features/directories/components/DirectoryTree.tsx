import { ChevronDown, ChevronRight, Folder, FolderOpen, MoreHorizontal } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import type { DirectoryTreeNode } from '@/features/directories/types'
import { cn } from '@/lib/utils'

export interface DirectoryActions {
  onCreateChild: (parent: DirectoryTreeNode) => void
  onRename: (node: DirectoryTreeNode) => void
  onMove: (node: DirectoryTreeNode) => void
  onDelete: (node: DirectoryTreeNode) => void
  onManagePermissions?: (node: DirectoryTreeNode) => void
}

interface DirectoryTreeProps {
  projectId: string
  tree: DirectoryTreeNode[]
  selectedId?: string
  canWrite: boolean
  canManage: boolean
  isAdmin: boolean
  actions: DirectoryActions
}

export function DirectoryTree({
  projectId,
  tree,
  selectedId,
  canWrite,
  canManage,
  isAdmin,
  actions,
}: DirectoryTreeProps) {
  if (tree.length === 0) {
    return (
      <p className="px-2 py-4 text-sm text-muted-foreground">
        No directories yet.
      </p>
    )
  }

  return (
    <ul className="space-y-0.5 text-sm" role="tree">
      {tree.map((node) => (
        <TreeNode
          key={node.id}
          projectId={projectId}
          node={node}
          depth={0}
          selectedId={selectedId}
          canWrite={canWrite}
          canManage={canManage}
          isAdmin={isAdmin}
          actions={actions}
        />
      ))}
    </ul>
  )
}

function TreeNode({
  projectId,
  node,
  depth,
  selectedId,
  canWrite,
  canManage,
  isAdmin,
  actions,
}: {
  projectId: string
  node: DirectoryTreeNode
  depth: number
  selectedId?: string
  canWrite: boolean
  canManage: boolean
  isAdmin: boolean
  actions: DirectoryActions
}) {
  const [open, setOpen] = useState(depth < 2 || node.is_root)
  const hasChildren = node.children.length > 0
  const selected = node.id === selectedId
  const Icon = open && hasChildren ? FolderOpen : Folder

  return (
    <li role="treeitem" aria-expanded={hasChildren ? open : undefined}>
      <div
        className={cn(
          'group flex items-center gap-0.5 rounded-md pr-1 transition-colors',
          selected
            ? 'bg-sidebar-accent text-sidebar-accent-foreground'
            : 'hover:bg-muted/70',
        )}
        style={{ paddingLeft: `${depth * 12 + 4}px` }}
      >
        <button
          type="button"
          className="flex size-6 shrink-0 items-center justify-center rounded text-muted-foreground"
          onClick={() => hasChildren && setOpen((v) => !v)}
          aria-label={open ? 'Collapse' : 'Expand'}
          disabled={!hasChildren}
        >
          {hasChildren ? (
            open ? (
              <ChevronDown className="size-3.5" />
            ) : (
              <ChevronRight className="size-3.5" />
            )
          ) : (
            <span className="size-3.5" />
          )}
        </button>

        <Link
          to={`/projects/${projectId}/directories/${node.id}`}
          className="flex min-w-0 flex-1 items-center gap-2 py-1.5"
        >
          <Icon className="size-4 shrink-0 text-[oklch(0.55_0.08_65)]" />
          <span className="truncate font-medium">{node.name}</span>
        </Link>

        {(canWrite || canManage || isAdmin) && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon-sm"
                className="opacity-0 group-hover:opacity-100 data-[state=open]:opacity-100"
                aria-label={`Actions for ${node.name}`}
              >
                <MoreHorizontal className="size-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {canWrite ? (
                <DropdownMenuItem onClick={() => actions.onCreateChild(node)}>
                  New child folder
                </DropdownMenuItem>
              ) : null}
              {canWrite && !node.is_root ? (
                <DropdownMenuItem onClick={() => actions.onRename(node)}>
                  Rename
                </DropdownMenuItem>
              ) : null}
              {canWrite && !node.is_root ? (
                <DropdownMenuItem onClick={() => actions.onMove(node)}>
                  Move…
                </DropdownMenuItem>
              ) : null}
              {isAdmin && actions.onManagePermissions ? (
                <DropdownMenuItem
                  onClick={() => actions.onManagePermissions?.(node)}
                >
                  Permissions…
                </DropdownMenuItem>
              ) : null}
              {canManage && !node.is_root ? (
                <>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    variant="destructive"
                    onClick={() => actions.onDelete(node)}
                  >
                    Delete…
                  </DropdownMenuItem>
                </>
              ) : null}
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </div>

      {open && hasChildren ? (
        <ul role="group">
          {node.children.map((child) => (
            <TreeNode
              key={child.id}
              projectId={projectId}
              node={child}
              depth={depth + 1}
              selectedId={selectedId}
              canWrite={canWrite}
              canManage={canManage}
              isAdmin={isAdmin}
              actions={actions}
            />
          ))}
        </ul>
      ) : null}
    </li>
  )
}
