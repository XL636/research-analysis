import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { Inbox } from 'lucide-react'
import EmptyState from '../EmptyState'

describe('EmptyState', () => {
  it('renders title and description', () => {
    render(
      <EmptyState
        icon={Inbox}
        title="No results"
        description="Try a different search term."
      />
    )
    expect(screen.getByText('No results')).toBeInTheDocument()
    expect(screen.getByText('Try a different search term.')).toBeInTheDocument()
  })

  it('renders the icon', () => {
    const { container } = render(
      <EmptyState
        icon={Inbox}
        title="Empty"
        description="Nothing here."
      />
    )
    const svg = container.querySelector('svg')
    expect(svg).toBeInTheDocument()
  })

  it('renders action when provided', () => {
    render(
      <EmptyState
        icon={Inbox}
        title="No items"
        description="Get started by adding an item."
        action={<button>Add Item</button>}
      />
    )
    expect(screen.getByText('Add Item')).toBeInTheDocument()
  })

  it('does not render action when not provided', () => {
    render(
      <EmptyState
        icon={Inbox}
        title="No items"
        description="Nothing to see."
      />
    )
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })
})
