import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { searchDocuments } from '../api/knowledge'

export function useSearch(initialQuery = '') {
  const [query, setQuery] = useState(initialQuery)
  const [debouncedQuery, setDebouncedQuery] = useState(initialQuery)

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(query), 300)
    return () => clearTimeout(timer)
  }, [query])

  const results = useQuery({
    queryKey: ['search', debouncedQuery],
    queryFn: () => searchDocuments(debouncedQuery),
    enabled: debouncedQuery.length > 0,
  })

  return { query, setQuery, results }
}
