import { api } from '@/lib/api'
import type { Command, CommandInput } from '@/features/commands/types'

export async function fetchDirectoryCommands(
  directoryId: string,
): Promise<Command[]> {
  const { data } = await api.get<Command[]>(
    `/directories/${directoryId}/commands`,
  )
  return data
}

export async function createCommand(
  directoryId: string,
  body: CommandInput,
): Promise<Command> {
  const { data } = await api.post<Command>(
    `/directories/${directoryId}/commands`,
    body,
  )
  return data
}

export async function updateCommand(
  commandId: string,
  body: Partial<CommandInput>,
): Promise<Command> {
  const { data } = await api.patch<Command>(`/commands/${commandId}`, body)
  return data
}

export async function deleteCommand(commandId: string): Promise<void> {
  await api.delete(`/commands/${commandId}`)
}
