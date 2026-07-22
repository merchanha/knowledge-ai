export interface Command {
  id: string
  directory_id: string
  title: string
  content: string
  metadata: Record<string, unknown>
}

export interface CommandInput {
  title: string
  content: string
  metadata?: Record<string, unknown>
}
