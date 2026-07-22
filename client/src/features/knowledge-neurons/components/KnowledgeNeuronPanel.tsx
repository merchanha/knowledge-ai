import { useState } from 'react'

import { DeleteKnowledgeNeuronDialog } from '@/features/knowledge-neurons/components/DeleteKnowledgeNeuronDialog'
import { KnowledgeNeuronFormDialog } from '@/features/knowledge-neurons/components/KnowledgeNeuronFormDialog'
import { KnowledgeNeuronList } from '@/features/knowledge-neurons/components/KnowledgeNeuronList'
import {
  useKnowledgeNeuronMutations,
  useKnowledgeNeurons,
} from '@/features/knowledge-neurons/hooks/use-knowledge-neurons'
import type { KnowledgeNeuron } from '@/features/knowledge-neurons/types'
import { getApiErrorMessage } from '@/lib/errors'
import { toast } from '@/lib/toast'

type DialogState =
  | { type: 'idle' }
  | { type: 'create' }
  | { type: 'edit'; neuron: KnowledgeNeuron }
  | { type: 'delete'; neuron: KnowledgeNeuron }

interface KnowledgeNeuronPanelProps {
  directoryId: string | undefined
  canWrite?: boolean
  canManage?: boolean
  filter?: string
}

export function KnowledgeNeuronPanel({
  directoryId,
  canWrite = true,
  canManage = false,
  filter = '',
}: KnowledgeNeuronPanelProps) {
  const { data: neurons = [], isLoading, isError, error } =
    useKnowledgeNeurons(directoryId)
  const mutations = useKnowledgeNeuronMutations(directoryId)
  const [dialog, setDialog] = useState<DialogState>({ type: 'idle' })

  const closeDialog = () => setDialog({ type: 'idle' })

  if (!directoryId) {
    return (
      <p className="text-sm text-muted-foreground">
        Select a folder to view KnowledgeNeurons.
      </p>
    )
  }

  if (isLoading) {
    return (
      <p className="text-sm text-muted-foreground">Loading KnowledgeNeurons…</p>
    )
  }

  if (isError) {
    return (
      <p className="text-sm text-destructive">
        Could not load KnowledgeNeurons: {getApiErrorMessage(error)}
      </p>
    )
  }

  return (
    <div className="space-y-4">
      <h3 className="font-heading text-lg">KnowledgeNeurons</h3>

      <KnowledgeNeuronList
        neurons={neurons}
        canWrite={canWrite}
        canManage={canManage}
        filter={filter}
        onCreate={canWrite ? () => setDialog({ type: 'create' }) : undefined}
        onEdit={(neuron) => setDialog({ type: 'edit', neuron })}
        onDelete={(neuron) => setDialog({ type: 'delete', neuron })}
      />

      <KnowledgeNeuronFormDialog
        open={dialog.type === 'create'}
        onOpenChange={(open) => !open && closeDialog()}
        title="New KnowledgeNeuron"
        description="Stored knowledge for this folder. Embedding runs in the background after save."
        confirmLabel="Create"
        pending={mutations.create.isPending}
        onSubmit={(values) => {
          mutations.create.mutate(values, {
            onSuccess: () => {
              toast.success('KnowledgeNeuron created')
              closeDialog()
            },
            onError: (err) =>
              toast.error(getApiErrorMessage(err, 'Create failed')),
          })
        }}
      />

      <KnowledgeNeuronFormDialog
        open={dialog.type === 'edit'}
        onOpenChange={(open) => !open && closeDialog()}
        title="Edit KnowledgeNeuron"
        description="Updating content re-queues embedding."
        confirmLabel="Save"
        pending={mutations.update.isPending}
        initial={
          dialog.type === 'edit'
            ? { title: dialog.neuron.title, content: dialog.neuron.content }
            : undefined
        }
        onSubmit={(values) => {
          if (dialog.type !== 'edit') return
          mutations.update.mutate(
            { neuronId: dialog.neuron.id, body: values },
            {
              onSuccess: () => {
                toast.success('KnowledgeNeuron updated')
                closeDialog()
              },
              onError: (err) =>
                toast.error(getApiErrorMessage(err, 'Update failed')),
            },
          )
        }}
      />

      <DeleteKnowledgeNeuronDialog
        open={dialog.type === 'delete'}
        onOpenChange={(open) => !open && closeDialog()}
        title={dialog.type === 'delete' ? dialog.neuron.title : ''}
        pending={mutations.remove.isPending}
        onConfirm={() => {
          if (dialog.type !== 'delete') return
          mutations.remove.mutate(dialog.neuron.id, {
            onSuccess: () => {
              toast.success('KnowledgeNeuron deleted')
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
