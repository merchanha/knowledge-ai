import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  createCommand,
  deleteCommand,
  fetchDirectoryCommands,
  updateCommand,
} from '@/features/commands/api/commands'
import type { CommandInput } from '@/features/commands/types'

export const commandKeys = {
  all: ['commands'] as const,
  list: (directoryId: string) => ['commands', 'list', directoryId] as const,
  detail: (id: string) => ['commands', 'detail', id] as const,
}

export function useCommands(directoryId: string | undefined) {
  return useQuery({
    queryKey: commandKeys.list(directoryId ?? ''),
    queryFn: () => fetchDirectoryCommands(directoryId!),
    enabled: Boolean(directoryId),
  })
}

export function useCommandMutations(directoryId: string | undefined) {
  const queryClient = useQueryClient()

  const invalidateList = () => {
    if (!directoryId) return
    void queryClient.invalidateQueries({
      queryKey: commandKeys.list(directoryId),
    })
  }

  const create = useMutation({
    mutationFn: (body: CommandInput) => createCommand(directoryId!, body),
    onSuccess: () => invalidateList(),
  })

  const update = useMutation({
    mutationFn: ({
      commandId,
      body,
    }: {
      commandId: string
      body: Partial<CommandInput>
    }) => updateCommand(commandId, body),
    onSuccess: () => invalidateList(),
  })

  const remove = useMutation({
    mutationFn: (commandId: string) => deleteCommand(commandId),
    onSuccess: () => invalidateList(),
  })

  return { create, update, remove }
}
