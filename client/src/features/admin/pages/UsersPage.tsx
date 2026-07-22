import { Link } from 'react-router-dom'

import { EmptyState } from '@/components/EmptyState'
import { LoadingState } from '@/components/LoadingState'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  useAdminUserMutations,
  useAdminUsers,
} from '@/features/admin/hooks/use-admin-users'
import { useCurrentUser } from '@/features/auth/hooks/use-auth'
import type { UserRole } from '@/features/auth/types'
import { getApiErrorMessage } from '@/lib/errors'
import { toast } from '@/lib/toast'

export function UsersPage() {
  const { data: me } = useCurrentUser()
  const isAdmin = me?.role === 'admin'
  const { data: users = [], isLoading, isError, error } = useAdminUsers(isAdmin)
  const { update } = useAdminUserMutations()

  if (!isAdmin) {
    return (
      <EmptyState
        title="Admin only"
        description="User management requires the application admin role."
        action={
          <Button asChild variant="outline" size="sm">
            <Link to="/projects">Back to projects</Link>
          </Button>
        }
      />
    )
  }

  if (isLoading) {
    return <LoadingState label="Loading users…" />
  }

  if (isError) {
    return (
      <p className="text-destructive">
        Could not load users: {getApiErrorMessage(error)}
      </p>
    )
  }

  return (
    <section className="animate-fade-up space-y-6">
      <div>
        <h1 className="font-heading text-3xl tracking-tight">Users</h1>
        <p className="mt-1 text-muted-foreground">
          Application-wide role and active status. Directory permissions are
          managed per folder.
        </p>
      </div>

      {users.length === 0 ? (
        <EmptyState title="No users" description="No accounts in the system yet." />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[36rem] text-left text-sm">
            <thead>
              <tr className="border-b border-border text-muted-foreground">
                <th className="py-2 pr-4 font-medium">Email</th>
                <th className="py-2 pr-4 font-medium">Name</th>
                <th className="py-2 pr-4 font-medium">Role</th>
                <th className="py-2 pr-4 font-medium">Active</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {users.map((user) => (
                <tr key={user.id}>
                  <td className="py-3 pr-4">{user.email}</td>
                  <td className="py-3 pr-4 text-muted-foreground">
                    {user.full_name ?? '—'}
                  </td>
                  <td className="py-3 pr-4">
                    <Select
                      value={user.role}
                      disabled={
                        update.isPending || user.id === me?.id
                      }
                      onValueChange={(role) =>
                        update.mutate(
                          {
                            userId: user.id,
                            body: { role: role as UserRole },
                          },
                          {
                            onSuccess: () => toast.success('Role updated'),
                            onError: (err) =>
                              toast.error(getApiErrorMessage(err)),
                          },
                        )
                      }
                    >
                      <SelectTrigger className="w-[7.5rem]">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="user">user</SelectItem>
                        <SelectItem value="admin">admin</SelectItem>
                      </SelectContent>
                    </Select>
                  </td>
                  <td className="py-3 pr-4">
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        className="size-4 accent-[oklch(0.45_0.08_65)]"
                        checked={user.is_active}
                        disabled={
                          update.isPending || user.id === me?.id
                        }
                        onChange={(e) =>
                          update.mutate(
                            {
                              userId: user.id,
                              body: { is_active: e.target.checked },
                            },
                            {
                              onSuccess: () =>
                                toast.success(
                                  e.target.checked
                                    ? 'User activated'
                                    : 'User deactivated',
                                ),
                              onError: (err) =>
                                toast.error(getApiErrorMessage(err)),
                            },
                          )
                        }
                      />
                      {user.is_active ? 'Yes' : 'No'}
                    </label>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
