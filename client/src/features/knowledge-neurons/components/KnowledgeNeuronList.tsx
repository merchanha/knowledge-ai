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
import type { KnowledgeNeuron } from '@/features/knowledge-neurons/types'

interface KnowledgeNeuronListProps {
  neurons: KnowledgeNeuron[]
  emptyMessage?: string
  canWrite?: boolean
  canManage?: boolean
  onCreate?: () => void
  onEdit?: (neuron: KnowledgeNeuron) => void
  onDelete?: (neuron: KnowledgeNeuron) => void
  similarityById?: Record<string, number>
  /** Client-side title/content filter (browse pages). */
  filter?: string
}

export function KnowledgeNeuronList({
  neurons,
  emptyMessage = 'No KnowledgeNeurons in this folder yet.',
  canWrite,
  canManage,
  onCreate,
  onEdit,
  onDelete,
  similarityById,
  filter = '',
}: KnowledgeNeuronListProps) {
  const needle = filter.trim().toLowerCase()
  const visible = needle
    ? neurons.filter(
        (n) =>
          n.title.toLowerCase().includes(needle) ||
          n.content.toLowerCase().includes(needle),
      )
    : neurons

  const showCreate = Boolean(canWrite && onCreate)
  const isEmpty = visible.length === 0

  if (isEmpty && !showCreate) {
    return (
      <p className="text-sm text-muted-foreground">
        {needle
          ? `No KnowledgeNeurons match “${filter.trim()}”.`
          : emptyMessage}
      </p>
    )
  }

  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
      {visible.map((neuron, index) => {
        const similarity = similarityById?.[neuron.id]
        const hasMenu =
          (canWrite && onEdit) || (canManage && onDelete)

        return (
          <div
            key={neuron.id}
            className="animate-card-in"
            style={{ animationDelay: `${Math.min(index, 8) * 40}ms` }}
          >
            <ItemCard
              typeLabel="KnowledgeNeuron"
              title={neuron.title}
              body={neuron.content}
              accent="neuron"
              chips={
                <>
                  {'has_embedding' in neuron ? (
                    <StatusChip
                      tone={neuron.has_embedding ? 'success' : 'pending'}
                    >
                      {neuron.has_embedding
                        ? 'Embedded'
                        : 'Embedding pending…'}
                    </StatusChip>
                  ) : null}
                  {similarity != null ? (
                    <StatusChip tone="default">
                      {(similarity * 100).toFixed(0)}% match
                    </StatusChip>
                  ) : null}
                </>
              }
              menu={
                hasMenu ? (
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        aria-label={`Actions for ${neuron.title}`}
                      >
                        <MoreHorizontal className="size-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      {canWrite && onEdit ? (
                        <DropdownMenuItem onClick={() => onEdit(neuron)}>
                          Edit
                        </DropdownMenuItem>
                      ) : null}
                      {canManage && onDelete ? (
                        <>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            variant="destructive"
                            onClick={() => onDelete(neuron)}
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
       {isEmpty && showCreate ? (
        <p className=" flex justify-center text-md text-muted-foreground sm:col-span-2 xl:col-span-3">
          {needle
            ? `No KnowledgeNeurons match “${filter.trim()}”.`
            : emptyMessage}
        </p>
      ) : null}
      {showCreate ? (
        <CreateItemCard
          label="New KnowledgeNeuron"
          onClick={onCreate!}
        />
      ) : null}
     
    </div>
  )
}
