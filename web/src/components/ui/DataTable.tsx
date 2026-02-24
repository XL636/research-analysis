import type { ReactNode } from 'react'
import { useTranslation } from 'react-i18next'

export interface Column<T> {
  key: string
  header: string
  render?: (row: T) => ReactNode
}

interface DataTableProps<T> {
  columns: Column<T>[]
  data: T[]
  onRowClick?: (row: T) => void
  selectable?: boolean
  selectedIds?: Set<number>
  onSelectionChange?: (ids: Set<number>) => void
  getRowId?: (row: T) => number
}

export default function DataTable<T extends object>({
  columns,
  data,
  onRowClick,
  selectable,
  selectedIds,
  onSelectionChange,
  getRowId,
}: DataTableProps<T>) {
  const { t } = useTranslation()

  const allIds = selectable && getRowId ? data.map(getRowId) : []
  const allSelected = selectable && allIds.length > 0 && selectedIds?.size === allIds.length

  const handleSelectAll = () => {
    if (!onSelectionChange) return
    if (allSelected) {
      onSelectionChange(new Set())
    } else {
      onSelectionChange(new Set(allIds))
    }
  }

  const handleSelectRow = (id: number) => {
    if (!onSelectionChange || !selectedIds) return
    const next = new Set(selectedIds)
    if (next.has(id)) {
      next.delete(id)
    } else {
      next.add(id)
    }
    onSelectionChange(next)
  }

  return (
    <div className="overflow-x-auto rounded-xl bg-surface-card shadow-sm">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200">
            {selectable && (
              <th className="w-10 px-3 py-3">
                <input
                  type="checkbox"
                  checked={allSelected}
                  onChange={handleSelectAll}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
              </th>
            )}
            {columns.map((col) => (
              <th
                key={col.key}
                className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500"
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {data.map((row, idx) => {
            const rowId = getRowId?.(row)
            const isSelected = rowId !== undefined && selectedIds?.has(rowId)
            return (
              <tr
                key={idx}
                className={`transition-colors duration-200 ${
                  isSelected ? 'bg-primary-50' : ''
                } ${
                  onRowClick
                    ? 'cursor-pointer hover:bg-gray-50'
                    : 'hover:bg-gray-50'
                }`}
              >
                {selectable && (
                  <td className="w-10 px-3 py-4">
                    <input
                      type="checkbox"
                      checked={isSelected || false}
                      onChange={() => rowId !== undefined && handleSelectRow(rowId)}
                      onClick={(e) => e.stopPropagation()}
                      className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                    />
                  </td>
                )}
                {columns.map((col) => (
                  <td
                    key={col.key}
                    className="px-6 py-4 text-primary-950"
                    onClick={() => onRowClick?.(row)}
                  >
                    {col.render
                      ? col.render(row)
                      : ((row as Record<string, unknown>)[col.key] as ReactNode)}
                  </td>
                ))}
              </tr>
            )
          })}
        </tbody>
      </table>
      {data.length === 0 && (
        <div className="px-6 py-12 text-center text-sm text-gray-400">
          {t('common.noData')}
        </div>
      )}
    </div>
  )
}
