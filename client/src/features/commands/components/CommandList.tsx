import { MoreHorizontal } from 'lucide-react'

import {
  CreateItemCard,
  ItemCard,
  StatusChip,
} from '@/components/ItemCard'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import type { Command } from '@/features/commands/types'

interface CommandListProps {
  commands: Command[]
  emptyMessage?: string
  canWrite?: boolean
  canManage?: boolean
  onCreate?: () => void
  onEdit?: (command: Command) => void
  onDelete?: (command: Command) => void
  filter?: string
}

export function CommandList({
  commands,
  emptyMessage = 'No Commands in this folder yet.',
  canWrite,
  canManage,
  onCreate,
  onEdit,
  onDelete,
  filter = '',
}: CommandListProps) {
  const needle = filter.trim().toLowerCase()
  const visible = needle
    ? commands.filter(
        (c) =>
          c.title.toLowerCase().includes(needle) ||
          c.content.toLowerCase().includes(needle),
      )
    : commands

  const showCreate = Boolean(canWrite && onCreate)
  const isEmpty = visible.length === 0

  if (isEmpty && !showCreate) {
    return (
      <p className="text-sm text-muted-foreground">
        {needle ? `No Commands match “${filter.trim()}”.` : emptyMessage}
      </p>
    )
  }

  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
      {visible.map((command, index) => {
        const hasMenu =
          (canWrite && onEdit) || (canManage && onDelete)

        return (
          <div
            key={command.id}
            className="animate-card-in"
            style={{ animationDelay: `${Math.min(index, 8) * 40}ms` }}
          >
            <ItemCard
              typeLabel="Command"
              title={command.title}
              body={command.content}
              accent="command"
              chips={<StatusChip tone="muted">Command</StatusChip>}
              menu={
                hasMenu ? (
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        aria-label={`Actions for ${command.title}`}
                      >
                        <MoreHorizontal className="size-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      {canWrite && onEdit ? (
                        <DropdownMenuItem onClick={() => onEdit(command)}>
                          Edit
                        </DropdownMenuItem>
                      ) : null}
                      {canManage && onDelete ? (
                        <>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            variant="destructive"
                            onClick={() => onDelete(command)}
                          >
                            Delete…
                          </DropdownMenuItem>
                        </>
                      ) : null}
                    </DropdownMenuContent>
                  </DropdownMenu>
                ) : null
              }
            />
          </div>
        )
      })}
      {showCreate ? (
        <CreateItemCard label="New Command" onClick={onCreate!} />
      ) : null}
      {isEmpty && showCreate ? (
        <p className="text-sm text-muted-foreground sm:col-span-2 xl:col-span-3">
          {needle ? `No Commands match “${filter.trim()}”.` : emptyMessage}
        </p>
      ) : null}
    </div>
  )
}
