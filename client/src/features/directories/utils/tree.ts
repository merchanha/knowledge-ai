import type { Directory, DirectoryTreeNode } from '@/features/directories/types'

/** Build a nested tree from the flat adjacency-list API response. */
export function buildDirectoryTree(flat: Directory[]): DirectoryTreeNode[] {
  const byId = new Map<string, DirectoryTreeNode>()
  for (const dir of flat) {
    byId.set(dir.id, { ...dir, children: [] })
  }

  const roots: DirectoryTreeNode[] = []
  for (const node of byId.values()) {
    if (node.parent_id && byId.has(node.parent_id)) {
      byId.get(node.parent_id)!.children.push(node)
    } else {
      roots.push(node)
    }
  }

  const sortRecursive = (nodes: DirectoryTreeNode[]) => {
    nodes.sort((a, b) => a.name.localeCompare(b.name))
    for (const n of nodes) {
      sortRecursive(n.children)
    }
  }
  sortRecursive(roots)
  return roots
}

/** Candidate move targets: exclude self and descendants (cycle prevention UX). */
export function listMoveTargets(
  flat: Directory[],
  movingId: string,
): Directory[] {
  const childrenByParent = new Map<string, string[]>()
  for (const dir of flat) {
    if (!dir.parent_id) continue
    const list = childrenByParent.get(dir.parent_id) ?? []
    list.push(dir.id)
    childrenByParent.set(dir.parent_id, list)
  }

  const blocked = new Set<string>([movingId])
  const stack = [movingId]
  while (stack.length) {
    const id = stack.pop()!
    for (const child of childrenByParent.get(id) ?? []) {
      if (!blocked.has(child)) {
        blocked.add(child)
        stack.push(child)
      }
    }
  }

  return flat.filter((d) => !blocked.has(d.id))
}
