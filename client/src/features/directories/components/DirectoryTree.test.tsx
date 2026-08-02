import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { DirectoryTree } from '@/features/directories/components/DirectoryTree'
import type { DirectoryTreeNode } from '@/features/directories/types'

const root: DirectoryTreeNode = {
  id: 'root-1',
  project_id: 'proj-1',
  parent_id: null,
  name: 'Root',
  is_root: true,
  children: [
    {
      id: 'docs-1',
      project_id: 'proj-1',
      parent_id: 'root-1',
      name: 'Docs',
      is_root: false,
      children: [],
    },
  ],
}

describe('DirectoryTree', () => {
  it('renders folder names and expands children', async () => {
    const user = userEvent.setup()
    const actions = {
      onCreateChild: vi.fn(),
      onRename: vi.fn(),
      onMove: vi.fn(),
      onDelete: vi.fn(),
    }

    render(
      <MemoryRouter>
        <DirectoryTree
          projectId="proj-1"
          tree={[root]}
          selectedId="docs-1"
          canWrite
          canManage
          isAdmin={false}
          actions={actions}
        />
      </MemoryRouter>,
    )

    expect(screen.getByText('Root')).toBeInTheDocument()
    expect(screen.getByText('Docs')).toBeInTheDocument()

    // Both nodes render an expand control; collapse the root (first).
    const [collapseRoot] = screen.getAllByRole('button', { name: 'Collapse' })
    await user.click(collapseRoot)
    expect(screen.queryByText('Docs')).not.toBeInTheDocument()
  })
})
