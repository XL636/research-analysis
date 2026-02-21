import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import MarkdownRenderer from '../MarkdownRenderer'

describe('MarkdownRenderer', () => {
  it('renders a simple paragraph', () => {
    render(<MarkdownRenderer content="Hello world" />)
    expect(screen.getByText('Hello world')).toBeInTheDocument()
  })

  it('renders a heading', () => {
    render(<MarkdownRenderer content="# Main Title" />)
    const heading = screen.getByRole('heading', { level: 1 })
    expect(heading).toBeInTheDocument()
    expect(heading).toHaveTextContent('Main Title')
  })

  it('renders an h2 heading', () => {
    render(<MarkdownRenderer content="## Section Title" />)
    const heading = screen.getByRole('heading', { level: 2 })
    expect(heading).toBeInTheDocument()
    expect(heading).toHaveTextContent('Section Title')
  })

  it('renders bold text', () => {
    render(<MarkdownRenderer content="This is **bold** text" />)
    expect(screen.getByText('bold')).toBeInTheDocument()
    expect(screen.getByText('bold').tagName).toBe('STRONG')
  })

  it('renders a link', () => {
    render(<MarkdownRenderer content="[Click here](https://example.com)" />)
    const link = screen.getByRole('link', { name: 'Click here' })
    expect(link).toBeInTheDocument()
    expect(link).toHaveAttribute('href', 'https://example.com')
    expect(link).toHaveAttribute('target', '_blank')
  })

  it('renders an unordered list', () => {
    const { container } = render(
      <MarkdownRenderer content={'- Item A\n- Item B\n- Item C'} />
    )
    const listItems = container.querySelectorAll('li')
    expect(listItems.length).toBe(3)
    expect(listItems[0]).toHaveTextContent('Item A')
    expect(listItems[1]).toHaveTextContent('Item B')
    expect(listItems[2]).toHaveTextContent('Item C')
  })

  it('renders with markdown-content wrapper class', () => {
    const { container } = render(<MarkdownRenderer content="Test" />)
    const wrapper = container.querySelector('.markdown-content')
    expect(wrapper).toBeInTheDocument()
  })
})
