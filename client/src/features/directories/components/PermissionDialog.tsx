import { useState } from 'react'

import { useAdminUsers } from '@/features/admin/hooks/use-admin-users'
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
import type { DirectoryPermission } from '@/features/directories/types'

interface PermissionDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  directoryName: string
  pending?: boolean
  onGrant: (userId: string, permission: DirectoryPermission) => void
  onRevoke: (userId: string, permission: DirectoryPermission) => void
}

const PERMISSIONS: DirectoryPermission[] = ['READ', 'WRITE', 'MANAGE']

export function PermissionDialog({
  open,
  onOpenChange,
  directoryName,
  pending,
  onGrant,
  onRevoke,
}: PermissionDialogProps) {
  const { data: users = [], isLoading } = useAdminUsers(open)
  const [userId, setUserId] = useState('')
  const [permission, setPermission] = useState<DirectoryPermission>('READ')

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (next) {
          setUserId('')
          setPermission('READ')
        }
        onOpenChange(next)
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Permissions — {directoryName}</DialogTitle>
          <DialogDescription>
            Admin only. Grant or revoke Casbin directory access for a user.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label>User</Label>
            <Select
              value={userId}
              onValueChange={setUserId}
              disabled={isLoading}
            >
              <SelectTrigger className="w-full">
                <SelectValue
                  placeholder={isLoading ? 'Loading users…' : 'Select user'}
                />
              </SelectTrigger>
              <SelectContent>
                {users.map((u) => (
                  <SelectItem key={u.id} value={u.id}>
                    {u.email}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Permission</Label>
            <Select
              value={permission}
              onValueChange={(v) => setPermission(v as DirectoryPermission)}
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {PERMISSIONS.map((p) => (
                  <SelectItem key={p} value={p}>
                    {p}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <DialogFooter className="gap-2 sm:gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
          <Button
            variant="outline"
            disabled={!userId || pending}
            onClick={() => onRevoke(userId, permission)}
          >
            Revoke
          </Button>
          <Button
            disabled={!userId || pending}
            onClick={() => onGrant(userId, permission)}
          >
            Grant
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
