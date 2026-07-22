import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  createKnowledgeNeuron,
  deleteKnowledgeNeuron,
  fetchDirectoryKnowledgeNeurons,
  searchKnowledgeNeurons,
  updateKnowledgeNeuron,
} from '@/features/knowledge-neurons/api/knowledge-neurons'
import type { KnowledgeNeuronInput } from '@/features/knowledge-neurons/types'

export const knowledgeNeuronKeys = {
  all: ['knowledge-neurons'] as const,
  list: (directoryId: string) =>
    ['knowledge-neurons', 'list', directoryId] as const,
  search: (term: string) =>
    ['knowledge-neurons', 'search', term] as const,
  detail: (id: string) => ['knowledge-neurons', 'detail', id] as const,
}

export function useKnowledgeNeurons(directoryId: string | undefined) {
  return useQuery({
    queryKey: knowledgeNeuronKeys.list(directoryId ?? ''),
    queryFn: () => fetchDirectoryKnowledgeNeurons(directoryId!),
    enabled: Boolean(directoryId),
    // Celery embeds asynchronously after create/update. Poll while any row
    // still lacks a vector so the chip flips to "Embedded" without a reload.
    refetchInterval: (query) => {
      const neurons = query.state.data
      if (!neurons?.some((n) => !n.has_embedding)) return false
      return 2_000
    },
  })
}

export function useKnowledgeNeuronSearch(searchTerm: string | undefined) {
  const trimmed = searchTerm?.trim() ?? ''
  return useQuery({
    queryKey: knowledgeNeuronKeys.search(trimmed),
    queryFn: () => searchKnowledgeNeurons(trimmed),
    enabled: trimmed.length > 0,
  })
}

export function useKnowledgeNeuronMutations(directoryId: string | undefined) {
  const queryClient = useQueryClient()

  const invalidateList = () => {
    if (!directoryId) return
    void queryClient.invalidateQueries({
      queryKey: knowledgeNeuronKeys.list(directoryId),
    })
  }

  const create = useMutation({
    mutationFn: (body: KnowledgeNeuronInput) =>
      createKnowledgeNeuron(directoryId!, body),
    onSuccess: () => invalidateList(),
  })

  const update = useMutation({
    mutationFn: ({
      neuronId,
      body,
    }: {
      neuronId: string
      body: Partial<KnowledgeNeuronInput>
    }) => updateKnowledgeNeuron(neuronId, body),
    onSuccess: () => invalidateList(),
  })

  const remove = useMutation({
    mutationFn: (neuronId: string) => deleteKnowledgeNeuron(neuronId),
    onSuccess: () => invalidateList(),
  })

  return { create, update, remove }
}
