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
import type { CommandInput } from '@/features/commands/types'

interface CommandFormDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description: string
  confirmLabel: string
  pending?: boolean
  initial?: Partial<CommandInput>
  onSubmit: (values: CommandInput) => void
}

export function CommandFormDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel,
  pending,
  initial,
  onSubmit,
}: CommandFormDialogProps) {
  const [commandTitle, setCommandTitle] = useState(initial?.title ?? '')
  const [content, setContent] = useState(initial?.content ?? '')

  useEffect(() => {
    if (open) {
      setCommandTitle(initial?.title ?? '')
      setContent(initial?.content ?? '')
    }
  }, [open, initial?.title, initial?.content])

  const canSubmit = commandTitle.trim().length > 0 && content.trim().length > 0

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
              title: commandTitle.trim(),
              content: content.trim(),
            })
          }}
        >
          <div className="space-y-2">
            <Label htmlFor="command-title">Title</Label>
            <Input
              id="command-title"
              value={commandTitle}
              onChange={(e) => setCommandTitle(e.target.value)}
              maxLength={255}
              autoFocus
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="command-content">Content</Label>
            <textarea
              id="command-content"
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
