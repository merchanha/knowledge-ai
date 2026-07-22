export interface KnowledgeNeuron {
  id: string
  directory_id: string
  title: string
  content: string
  metadata: Record<string, unknown>
  has_embedding: boolean
}

export interface KnowledgeNeuronSearchResult {
  id: string
  directory_id: string
  title: string
  content: string
  metadata: Record<string, unknown>
  similarity: number
}

export interface KnowledgeNeuronInput {
  title: string
  content: string
  metadata?: Record<string, unknown>
}
