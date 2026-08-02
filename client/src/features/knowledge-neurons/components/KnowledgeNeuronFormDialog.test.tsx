import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { KnowledgeNeuronFormDialog } from '@/features/knowledge-neurons/components/KnowledgeNeuronFormDialog'

describe('KnowledgeNeuronFormDialog', () => {
  it('submits trimmed title and content', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()

    render(
      <KnowledgeNeuronFormDialog
        open
        onOpenChange={vi.fn()}
        title="Create KnowledgeNeuron"
        description="Add a document"
        confirmLabel="Create"
        onSubmit={onSubmit}
      />,
    )

    await user.type(screen.getByLabelText('Title'), '  Auth notes  ')
    await user.type(screen.getByLabelText('Content'), '  Use JWT blacklist  ')
    await user.click(screen.getByRole('button', { name: 'Create' }))

    expect(onSubmit).toHaveBeenCalledWith({
      title: 'Auth notes',
      content: 'Use JWT blacklist',
    })
  })

  it('disables submit until both fields are filled', () => {
    render(
      <KnowledgeNeuronFormDialog
        open
        onOpenChange={vi.fn()}
        title="Create KnowledgeNeuron"
        description="Add a document"
        confirmLabel="Create"
        onSubmit={vi.fn()}
      />,
    )

    expect(screen.getByRole('button', { name: 'Create' })).toBeDisabled()
  })
})
