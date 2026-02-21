import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import SearchInput from '../SearchInput'

describe('SearchInput', () => {
  it('renders with default placeholder', () => {
    render(<SearchInput value="" onChange={() => {}} />)
    expect(screen.getByPlaceholderText('common.search')).toBeInTheDocument()
  })

  it('renders with custom placeholder', () => {
    render(
      <SearchInput value="" onChange={() => {}} placeholder="Find papers..." />
    )
    expect(screen.getByPlaceholderText('Find papers...')).toBeInTheDocument()
  })

  it('displays the current value', () => {
    render(<SearchInput value="test query" onChange={() => {}} />)
    const input = screen.getByPlaceholderText('common.search') as HTMLInputElement
    expect(input.value).toBe('test query')
  })

  it('fires onChange callback when typing', () => {
    const handleChange = vi.fn()
    render(<SearchInput value="" onChange={handleChange} />)
    const input = screen.getByPlaceholderText('common.search')
    fireEvent.change(input, { target: { value: 'hello' } })
    expect(handleChange).toHaveBeenCalledWith('hello')
  })

  it('renders as a text input', () => {
    render(<SearchInput value="" onChange={() => {}} />)
    const input = screen.getByPlaceholderText('common.search') as HTMLInputElement
    expect(input.type).toBe('text')
  })
})
