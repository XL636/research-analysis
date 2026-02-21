import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import ProgressStepper from '../ProgressStepper'

describe('ProgressStepper', () => {
  const steps = [
    { name: 'Parse', status: 'completed' as const },
    { name: 'Analyze', status: 'running' as const },
    { name: 'Review', status: 'pending' as const },
  ]

  it('renders all step names', () => {
    render(<ProgressStepper steps={steps} />)
    expect(screen.getByText('Parse')).toBeInTheDocument()
    expect(screen.getByText('Analyze')).toBeInTheDocument()
    expect(screen.getByText('Review')).toBeInTheDocument()
  })

  it('renders correct status labels', () => {
    render(<ProgressStepper steps={steps} />)
    expect(screen.getByText('Completed')).toBeInTheDocument()
    expect(screen.getByText('Running')).toBeInTheDocument()
    expect(screen.getByText('Pending')).toBeInTheDocument()
  })

  it('renders error status', () => {
    const errorSteps = [
      { name: 'Validate', status: 'error' as const },
    ]
    render(<ProgressStepper steps={errorSteps} />)
    expect(screen.getByText('Validate')).toBeInTheDocument()
    expect(screen.getByText('Error')).toBeInTheDocument()
  })

  it('renders the correct number of steps', () => {
    const { container } = render(<ProgressStepper steps={steps} />)
    const svgs = container.querySelectorAll('svg')
    expect(svgs.length).toBe(steps.length)
  })

  it('renders single step without connecting line', () => {
    const singleStep = [{ name: 'Only Step', status: 'pending' as const }]
    render(<ProgressStepper steps={singleStep} />)
    expect(screen.getByText('Only Step')).toBeInTheDocument()
    expect(screen.getByText('Pending')).toBeInTheDocument()
  })
})
