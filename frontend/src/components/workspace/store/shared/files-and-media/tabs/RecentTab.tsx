'use client'

import { useEffect } from 'react'
import { useRecentMedia } from '../hooks/useRecentMedia'
import { MediaGrid } from '../MediaGrid'
import type { MediaType, MediaItem } from '../types'

interface RecentTabProps {
  selectedIds: Set<string>
  onToggleSelect: (uploadId: string, item: MediaItem) => void
  allowedTypes?: MediaType[]
  maxSelection?: number
  refetchRef?: React.MutableRefObject<(() => void) | null>
}

export function RecentTab({
  selectedIds,
  onToggleSelect,
  allowedTypes,
  maxSelection,
  refetchRef,
}: RecentTabProps) {
  const { recentMedia, loading, error, refetch } = useRecentMedia({
    limit: 50,
  })

  // Expose refetch function to parent via ref
  useEffect(() => {
    if (refetchRef) {
      refetchRef.current = refetch
    }
  }, [refetch, refetchRef])

  // Filter by allowed types
  const filteredMedia = allowedTypes
    ? recentMedia.filter((item) => allowedTypes.includes(item.type))
    : recentMedia

  // Wrapper to pass both uploadId and item
  const handleToggleSelect = (uploadId: string) => {
    const item = filteredMedia.find((i) => i.uploadId === uploadId)
    if (item) {
      onToggleSelect(uploadId, item)
    }
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-destructive">Failed to load recent media</p>
        <button
          onClick={() => refetch()}
          className="mt-2 text-sm text-primary hover:underline"
        >
          Try again
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          {selectedIds.size > 0
            ? `${selectedIds.size} selected`
            : `${filteredMedia.length} recent files`}
        </p>
        {selectedIds.size > 0 && (
          <button
            onClick={() => {
              selectedIds.forEach((id) => handleToggleSelect(id))
            }}
            className="text-sm text-primary hover:underline"
          >
            Clear selection
          </button>
        )}
      </div>

      <MediaGrid
        items={filteredMedia}
        selectedIds={selectedIds}
        onToggleSelect={handleToggleSelect}
        maxSelection={maxSelection}
        loading={loading}
      />
    </div>
  )
}
