import { useState } from 'react'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import type { Directory } from '@/features/directories/types'

interface MoveDirectoryDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  directoryName: string
  targets: Directory[]
  pending?: boolean
  onSubmit: (newParentId: string) => void
}

export function MoveDirectoryDialog({
  open,
  onOpenChange,
  directoryName,
  targets,
  pending,
  onSubmit,
}: MoveDirectoryDialogProps) {
  const [parentId, setParentId] = useState<string>('')

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (next) setParentId('')
        onOpenChange(next)
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Move “{directoryName}”</DialogTitle>
          <DialogDescription>
            Choose a new parent within this project. Roots and descendants of
            this folder are excluded.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-2">
          <Label>New parent</Label>
          <Select
            value={parentId || undefined}
            onValueChange={(value) => setParentId(value ?? '')}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Select folder" />
            </SelectTrigger>
            <SelectContent>
              {targets.map((t) => (
                <SelectItem key={t.id} value={t.id}>
                  {t.name}
                  {t.is_root ? ' (root)' : ''}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            disabled={!parentId || pending}
            onClick={() => onSubmit(parentId)}
          >
            Move
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
