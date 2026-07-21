# 03 — Feature Module Structure

## What We Built

Week 17 adds the directories feature: a nested tree UI built from the flat adjacency-list API, breadcrumbs, create/rename/move/delete dialogs, and an admin permission grant/revoke dialog. Hooks (`useDirectoryTree`, `useBreadcrumbs`, `useDirectoryMutations`) own fetching and cache invalidation; `DirectoriesPage` stays compositional.

## Key Concepts

### Colocation

```
features/directories/
  api/directories.ts     # thin Axios wrappers
  types.ts
  utils/tree.ts          # pure helpers (build tree, move targets)
  hooks/use-directory-tree.ts  # Query + mutations
  components/            # tree, breadcrumbs, dialogs
  pages/DirectoriesPage.tsx    # wires hooks + dialogs
```

Shared UI (Button, Dialog) stays in `components/ui`. Cross-feature types (User) stay in `features/auth`. Avoid dumping everything into a flat feature folder or a giant top-level `hooks/` directory.

### Directory tree UI patterns

The API returns a **flat list** with `parent_id` (adjacency list). The client builds a nested `DirectoryTreeNode[]` once per fetch (`buildDirectoryTree`). Expand/collapse is local UI state on each node. Selection is the route param `:directoryId`.

Move dialogs exclude the node and its descendants so the UI does not offer cycle-creating targets (the API also rejects cycles).

### Custom hooks + optimistic updates

This week uses **invalidate-on-success** rather than full optimistic updates: after create/rename/move/delete, invalidate `['directories', 'tree', projectId]` (and breadcrumbs when needed). That is simpler and matches the backend as source of truth.

**Optimistic updates** (optional later) would `setQueryData` immediately, then roll back in `onError`. Use them when latency feels bad and the mutation is easy to reverse in the cache.

### Permission-gated UI

- **Admin** (`user.role === 'admin'`): can open the Permissions dialog (Casbin grant/revoke) and delete folders (`MANAGE` on the API).
- **Write actions** (create/rename/move): shown to members who can load the tree; the API still enforces Casbin — a 403 surfaces if the user lacks `WRITE`.
- Never rely on hiding a button as security — the API is the gate.

## Code Walkthrough

1. `hooks/use-directory-tree` — Query + `buildDirectoryTree`.
2. `components/DirectoryTree` — recursive nodes, action menu.
3. `pages/DirectoriesPage` — dialog state machine (`idle | create | rename | …`).
4. `components/PermissionDialog` — loads `/admin/users` only when open and caller is admin.

## Further Reading

- Backend: `api/docs/05-hierarchical-data-trees.md`, `api/docs/06-controller-service-separation.md`
- [TanStack Query mutations](https://tanstack.com/query/latest/docs/framework/react/guides/mutations)

## Exercises (Optional)

1. Add optimistic create: insert a temporary node, replace with the server id on success.
2. Disable write menu items when `/permissions/me` shows only `READ` for that directory.
