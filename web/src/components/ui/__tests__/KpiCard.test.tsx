import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { FileText } from 'lucide-react'
import KpiCard from '../KpiCard'

describe('KpiCard', () => {
  it('renders title and value', () => {
    render(<KpiCard title="Total Papers" value={42} icon={FileText} />)
    expect(screen.getByText('Total Papers')).toBeInTheDocument()
    expect(screen.getByText('42')).toBeInTheDocument()
  })

  it('renders string value', () => {
    render(<KpiCard title="Status" value="Active" icon={FileText} />)
    expect(screen.getByText('Active')).toBeInTheDocument()
  })

  it('renders trend when provided', () => {
    render(
      <KpiCard title="Papers" value={10} icon={FileText} trend="+5 this week" />
    )
    expect(screen.getByText('+5 this week')).toBeInTheDocument()
  })

  it('does not render trend when not provided', () => {
    render(<KpiCard title="Papers" value={10} icon={FileText} />)
    expect(screen.queryByText(/this week/)).not.toBeInTheDocument()
  })

  it('renders the icon', () => {
    const { container } = render(
      <KpiCard title="Papers" value={10} icon={FileText} />
    )
    const svg = container.querySelector('svg')
    expect(svg).toBeInTheDocument()
  })
})
