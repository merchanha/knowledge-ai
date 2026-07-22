# 04 — TanStack Query Patterns

## What We Built

Week 18 adds the KnowledgeNeuron feature module: list by directory, CRUD dialogs, and semantic search via `?search_term=`. Hooks own fetching and mutations; pages stay compositional. Commands (Week 19) reuse the same Query patterns without search.

## Key Concepts

### Server state vs UI state

| Kind | Who owns it | Examples |
|------|-------------|----------|
| **Server state** | TanStack Query | KnowledgeNeuron lists, search results, project members |
| **Client/UI state** | `useState` / route params | Which dialog is open, search input draft, selected folder |

Do **not** put API lists in Zustand. Query already caches, dedupes, and refetches. Local state is for “which modal am I looking at?”

### Query keys as a contract

Keys are hierarchical arrays. Treat them like a filesystem path:

```ts
export const knowledgeNeuronKeys = {
  all: ['knowledge-neurons'] as const,
  list: (directoryId: string) =>
    ['knowledge-neurons', 'list', directoryId] as const,
  search: (term: string) =>
    ['knowledge-neurons', 'search', term] as const,
  detail: (id: string) =>
    ['knowledge-neurons', 'detail', id] as const,
}
```

- `invalidateQueries({ queryKey: ['knowledge-neurons'] })` refreshes **all** neuron queries.
- `invalidateQueries({ queryKey: knowledgeNeuronKeys.list(dirId) })` refreshes only that directory’s list.

Always export a `*Keys` object from the feature hook file so mutations and pages share the same strings.

### Mutations + cache invalidation

Default pattern in this SPA: **mutate → invalidate on success**.

```ts
const create = useMutation({
  mutationFn: (body) => createKnowledgeNeuron(directoryId, body),
  onSuccess: () => {
    void queryClient.invalidateQueries({
      queryKey: knowledgeNeuronKeys.list(directoryId),
    })
  },
})
```

After create/update/delete, the list refetch is the source of truth. Simpler than hand-editing the cache, and correct when the API adds fields (e.g. `has_embedding`).

### Invalidation vs optimistic updates

| Approach | When to use |
|----------|-------------|
| **Invalidate on success** | Default. Lists are small; correctness > snappiness. |
| **Optimistic update** | Latency feels bad *and* you can reverse the cache on error (`onMutate` → `setQueryData` → `onError` rollback). |

We use invalidation for KnowledgeNeurons. Search results are **not** invalidated by CRUD (different key); clearing search or waiting for re-embed is intentional — embeddings are async via Celery.

### Semantic search UX

- List mode: `GET /directories/{id}/knowledge-neurons` when a folder is selected.
- Search mode: `GET /knowledge-neurons?search_term=…` (permission-scoped across readable directories).
- Keep the search term in the **URL** (`?q=…`) so refresh/share works; the Query key includes that term.

Search ranking uses Voyage embeddings + pgvector cosine similarity. A newly created neuron may not appear in search until the Celery worker finishes embedding (`has_embedding` on the list item).

The list query **polls every 2s** while any neuron in that folder still has `has_embedding: false`, then stops — so the chip updates to “Embedded” without a manual reload.

## Code Walkthrough

1. `features/knowledge-neurons/api/knowledge-neurons.ts` — thin Axios wrappers.
2. `hooks/use-knowledge-neurons.ts` — `useKnowledgeNeurons`, `useKnowledgeNeuronSearch`, `useKnowledgeNeuronMutations`.
3. `pages/KnowledgeNeuronsPage.tsx` — project picker / directory tree + list + search.
4. Directory detail pane embeds the same list when you select a folder under `/projects/:id/directories/:directoryId`.

## Further Reading

- [TanStack Query — Mutations](https://tanstack.com/query/latest/docs/framework/react/guides/mutations)
- [Query Keys](https://tanstack.com/query/latest/docs/framework/react/guides/query-keys)
- Backend: `api/docs/09-vector-search-pgvector.md`

## Exercises (Optional)

1. After create, optimistically prepend a temporary neuron, then replace with the server response.
2. Poll `has_embedding` until true, then enable a “Search now” hint.
