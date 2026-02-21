import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import Badge from '../Badge'

describe('Badge', () => {
  it('renders children text', () => {
    render(<Badge>Test</Badge>)
    expect(screen.getByText('Test')).toBeInTheDocument()
  })

  it('applies default variant classes', () => {
    render(<Badge>Default</Badge>)
    const el = screen.getByText('Default')
    expect(el.className).toContain('bg-gray-100')
  })

  it('applies primary variant', () => {
    render(<Badge variant="primary">Primary</Badge>)
    expect(screen.getByText('Primary').className).toContain('bg-primary-100')
  })

  it('applies accent variant', () => {
    render(<Badge variant="accent">Accent</Badge>)
    expect(screen.getByText('Accent').className).toContain('bg-emerald-100')
  })
})
