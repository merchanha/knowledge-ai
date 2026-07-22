import { useState } from 'react'

import { CommandFormDialog } from '@/features/commands/components/CommandFormDialog'
import { CommandList } from '@/features/commands/components/CommandList'
import { DeleteCommandDialog } from '@/features/commands/components/DeleteCommandDialog'
import {
  useCommandMutations,
  useCommands,
} from '@/features/commands/hooks/use-commands'
import type { Command } from '@/features/commands/types'
import { getApiErrorMessage } from '@/lib/errors'
import { toast } from '@/lib/toast'

type DialogState =
  | { type: 'idle' }
  | { type: 'create' }
  | { type: 'edit'; command: Command }
  | { type: 'delete'; command: Command }

interface CommandPanelProps {
  directoryId: string | undefined
  canWrite?: boolean
  canManage?: boolean
  filter?: string
}

export function CommandPanel({
  directoryId,
  canWrite = true,
  canManage = false,
  filter = '',
}: CommandPanelProps) {
  const { data: commands = [], isLoading, isError, error } =
    useCommands(directoryId)
  const mutations = useCommandMutations(directoryId)
  const [dialog, setDialog] = useState<DialogState>({ type: 'idle' })

  const closeDialog = () => setDialog({ type: 'idle' })

  if (!directoryId) {
    return (
      <p className="text-sm text-muted-foreground">
        Select a folder to view Commands.
      </p>
    )
  }

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Loading Commands…</p>
  }

  if (isError) {
    return (
      <p className="text-sm text-destructive">
        Could not load Commands: {getApiErrorMessage(error)}
      </p>
    )
  }

  return (
    <div className="space-y-4">
      <h3 className="font-heading text-lg">Commands</h3>

      <CommandList
        commands={commands}
        canWrite={canWrite}
        canManage={canManage}
        filter={filter}
        onCreate={canWrite ? () => setDialog({ type: 'create' }) : undefined}
        onEdit={(command) => setDialog({ type: 'edit', command })}
        onDelete={(command) => setDialog({ type: 'delete', command })}
      />

      <CommandFormDialog
        open={dialog.type === 'create'}
        onOpenChange={(open) => !open && closeDialog()}
        title="New Command"
        description="Reusable instruction snippet for agents and teammates. No embeddings."
        confirmLabel="Create"
        pending={mutations.create.isPending}
        onSubmit={(values) => {
          mutations.create.mutate(values, {
            onSuccess: () => {
              toast.success('Command created')
              closeDialog()
            },
            onError: (err) =>
              toast.error(getApiErrorMessage(err, 'Create failed')),
          })
        }}
      />

      <CommandFormDialog
        open={dialog.type === 'edit'}
        onOpenChange={(open) => !open && closeDialog()}
        title="Edit Command"
        description="Update the instruction text stored in this folder."
        confirmLabel="Save"
        pending={mutations.update.isPending}
        initial={
          dialog.type === 'edit'
            ? { title: dialog.command.title, content: dialog.command.content }
            : undefined
        }
        onSubmit={(values) => {
          if (dialog.type !== 'edit') return
          mutations.update.mutate(
            { commandId: dialog.command.id, body: values },
            {
              onSuccess: () => {
                toast.success('Command updated')
                closeDialog()
              },
              onError: (err) =>
                toast.error(getApiErrorMessage(err, 'Update failed')),
            },
          )
        }}
      />

      <DeleteCommandDialog
        open={dialog.type === 'delete'}
        onOpenChange={(open) => !open && closeDialog()}
        title={dialog.type === 'delete' ? dialog.command.title : ''}
        pending={mutations.remove.isPending}
        onConfirm={() => {
          if (dialog.type !== 'delete') return
          mutations.remove.mutate(dialog.command.id, {
            onSuccess: () => {
              toast.success('Command deleted')
              closeDialog()
            },
            onError: (err) =>
              toast.error(getApiErrorMessage(err, 'Delete failed')),
          })
        }}
      />
    </div>
  )
}
