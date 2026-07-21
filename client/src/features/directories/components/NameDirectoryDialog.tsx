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

interface NameDirectoryDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description: string
  initialName?: string
  confirmLabel: string
  pending?: boolean
  onSubmit: (name: string) => void
}

export function NameDirectoryDialog({
  open,
  onOpenChange,
  title,
  description,
  initialName = '',
  confirmLabel,
  pending,
  onSubmit,
}: NameDirectoryDialogProps) {
  const [name, setName] = useState(initialName)

  useEffect(() => {
    if (open) {
      setName(initialName)
    }
  }, [open, initialName])

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>
        <form
          className="space-y-4"
          onSubmit={(e) => {
            e.preventDefault()
            const trimmed = name.trim()
            if (!trimmed) return
            onSubmit(trimmed)
          }}
        >
          <div className="space-y-2">
            <Label htmlFor="directory-name">Name</Label>
            <Input
              id="directory-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoFocus
              maxLength={255}
              required
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
            <Button type="submit" disabled={pending || !name.trim()}>
              {confirmLabel}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
