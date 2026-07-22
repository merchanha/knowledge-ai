import { api } from '@/lib/api'
import type {
  KnowledgeNeuron,
  KnowledgeNeuronInput,
  KnowledgeNeuronSearchResult,
} from '@/features/knowledge-neurons/types'

export async function fetchDirectoryKnowledgeNeurons(
  directoryId: string,
): Promise<KnowledgeNeuron[]> {
  const { data } = await api.get<KnowledgeNeuron[]>(
    `/directories/${directoryId}/knowledge-neurons`,
  )
  return data
}

export async function searchKnowledgeNeurons(
  searchTerm: string,
  limit = 20,
): Promise<KnowledgeNeuronSearchResult[]> {
  const { data } = await api.get<KnowledgeNeuronSearchResult[]>(
    '/knowledge-neurons',
    { params: { search_term: searchTerm, limit } },
  )
  return data
}

export async function createKnowledgeNeuron(
  directoryId: string,
  body: KnowledgeNeuronInput,
): Promise<KnowledgeNeuron> {
  const { data } = await api.post<KnowledgeNeuron>(
    `/directories/${directoryId}/knowledge-neurons`,
    body,
  )
  return data
}

export async function updateKnowledgeNeuron(
  neuronId: string,
  body: Partial<KnowledgeNeuronInput>,
): Promise<KnowledgeNeuron> {
  const { data } = await api.patch<KnowledgeNeuron>(
    `/knowledge-neurons/${neuronId}`,
    body,
  )
  return data
}

export async function deleteKnowledgeNeuron(neuronId: string): Promise<void> {
  await api.delete(`/knowledge-neurons/${neuronId}`)
}
