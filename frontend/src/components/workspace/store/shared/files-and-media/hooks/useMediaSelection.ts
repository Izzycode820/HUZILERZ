/**
 * Hook for managing media selection state (multi-select)
 */

import { useState, useCallback } from 'react'
import type { MediaItem } from '../types'

export function useMediaSelection(maxSelection?: number) {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())

  const toggleSelect = useCallback(
    (uploadId: string) => {
      setSelectedIds((prev) => {
        const next = new Set(prev)

        if (next.has(uploadId)) {
          // Deselect
          next.delete(uploadId)
        } else {
          // Select (if not at max)
          if (!maxSelection || next.size < maxSelection) {
            next.add(uploadId)
          }
        }

        return next
      })
    },
    [maxSelection]
  )

  const selectAll = useCallback((items: MediaItem[]) => {
    const ids = items.map((item) => item.uploadId)
    if (maxSelection) {
      setSelectedIds(new Set(ids.slice(0, maxSelection)))
    } else {
      setSelectedIds(new Set(ids))
    }
  }, [maxSelection])

  const clearSelection = useCallback(() => {
    setSelectedIds(new Set())
  }, [])

  const isSelected = useCallback(
    (uploadId: string) => {
      return selectedIds.has(uploadId)
    },
    [selectedIds]
  )

  const canSelectMore = useCallback(() => {
    if (!maxSelection) return true
    return selectedIds.size < maxSelection
  }, [selectedIds.size, maxSelection])

  return {
    selectedIds,
    toggleSelect,
    selectAll,
    clearSelection,
    isSelected,
    canSelectMore,
    selectedCount: selectedIds.size,
  }
}
