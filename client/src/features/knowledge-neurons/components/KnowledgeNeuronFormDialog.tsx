import { useEffect, useState } from 'react'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import type { KnowledgeNeuronInput } from '@/features/knowledge-neurons/types'

interface KnowledgeNeuronFormDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description: string
  confirmLabel: string
  pending?: boolean
  initial?: Partial<KnowledgeNeuronInput>
  onSubmit: (values: KnowledgeNeuronInput) => void
}

export function KnowledgeNeuronFormDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel,
  pending,
  initial,
  onSubmit,
}: KnowledgeNeuronFormDialogProps) {
  const [neuronTitle, setNeuronTitle] = useState(initial?.title ?? '')
  const [content, setContent] = useState(initial?.content ?? '')

  useEffect(() => {
    if (open) {
      setNeuronTitle(initial?.title ?? '')
      setContent(initial?.content ?? '')
    }
  }, [open, initial?.title, initial?.content])

  const canSubmit = neuronTitle.trim().length > 0 && content.trim().length > 0

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>
        <form
          className="space-y-4"
          onSubmit={(e) => {
            e.preventDefault()
            if (!canSubmit) return
            onSubmit({
              title: neuronTitle.trim(),
              content: content.trim(),
            })
          }}
        >
          <div className="space-y-2">
            <Label htmlFor="neuron-title">Title</Label>
            <Input
              id="neuron-title"
              value={neuronTitle}
              onChange={(e) => setNeuronTitle(e.target.value)}
              maxLength={255}
              autoFocus
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="neuron-content">Content</Label>
            <textarea
              id="neuron-content"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              required
              rows={8}
              className="border-input bg-background placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-ring/50 w-full rounded-md border px-3 py-2 text-sm outline-none focus-visible:ring-[3px]"
            />
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={pending || !canSubmit}>
              {confirmLabel}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
