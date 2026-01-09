'use client'

import { useState, useRef, useEffect } from 'react'
import { UploadZone } from './UploadZone'
import { MediaGrid } from './MediaGrid'
import { useMediaUpload } from './hooks/useMediaUpload'
import { useRecentMedia } from './hooks/useRecentMedia'
import { useMediaDelete } from './hooks/useMediaDelete'
import type { MediaType, MediaItem } from './types'

interface MediaLibraryProps {
  /** Selected item IDs */
  selectedIds: Set<string>

  /** Selection toggle handler */
  onToggleSelect: (uploadId: string, item: MediaItem) => void

  /** Allowed media types */
  allowedTypes?: MediaType[]

  /** Maximum selection */
  maxSelection?: number

  /** Search query */
  search?: string

  /** Sort by */
  sortBy?: 'date' | 'name' | 'size'

  /** Sort order */
  sortOrder?: 'asc' | 'desc'

  /** View mode */
  viewMode?: 'grid' | 'list'

  /** Callback when new items are uploaded */
  onUploadsComplete?: (items: MediaItem[]) => void

  /** Callback to expose clearUploads for modal close */
  onClearUploads?: (clearFn: () => void) => void
}

export function MediaLibrary({
  selectedIds,
  onToggleSelect,
  allowedTypes = ['image', 'video', '3d_model'],
  maxSelection,
  search,
  sortBy = 'date',
  sortOrder = 'desc',
  viewMode = 'grid',
  onUploadsComplete,
  onClearUploads,
}: MediaLibraryProps) {
  const { uploads, uploadMultiple, clearUploads } = useMediaUpload()

  // Expose clearUploads to parent (for modal close)
  useEffect(() => {
    if (onClearUploads) {
      onClearUploads(clearUploads)
    }
  }, [onClearUploads, clearUploads])

  // Track which items have been reported to prevent duplicates
  const reportedIdsRef = useRef<Set<string>>(new Set())

  // Get media type filter from allowedTypes
  const mediaTypeFilter = allowedTypes.length === 1 ? allowedTypes[0] : undefined

  // Fetch recent media with search and filters
  const { recentMedia, loading, error, refetch } = useRecentMedia({
    limit: 100,
    mediaType: mediaTypeFilter,
    search,
    sortBy,
    sortOrder,
  })

  // Delete media handler
  const { deleteMedia } = useMediaDelete(refetch)

  // Get optimistic items from uploads (Shopify pattern)
  const optimisticItems = uploads
    .map((u) => u.result)
    .filter((item): item is MediaItem => item !== null && item !== undefined)

  // Notify parent when uploads complete (for selection tracking)
  useEffect(() => {
    const completedItems = optimisticItems.filter(
      (item) => item.status === 'ready' && !reportedIdsRef.current.has(item.uploadId)
    )

    if (completedItems.length > 0 && onUploadsComplete) {
      completedItems.forEach((item) => {
        reportedIdsRef.current.add(item.uploadId)
      })
      onUploadsComplete(completedItems)
    }
  }, [optimisticItems.length, onUploadsComplete])

  const handleFilesSelected = async (files: File[]) => {
    await uploadMultiple(files)
  }

  // Handle clear - also clear reported IDs
  const handleClear = () => {
    clearUploads()
    reportedIdsRef.current.clear()
  }

  // Wrapper to pass both uploadId and item
  const handleToggleSelect = (uploadId: string) => {
    const item = recentMedia.find((i) => i.uploadId === uploadId)
    if (item) {
      onToggleSelect(uploadId, item)
    }
  }

  // Delete handler
  const handleDelete = async (uploadId: string) => {
    await deleteMedia(uploadId)
  }

  // Filter by allowed types
  const filteredRecentMedia = allowedTypes
    ? recentMedia.filter((item) => allowedTypes.includes(item.type))
    : recentMedia

  // Merge optimistic uploads with recent media (Shopify pattern)
  // Optimistic items appear first, then DB items
  const mergedItems = [...optimisticItems, ...filteredRecentMedia]

  return (
    <div className="flex flex-col h-full space-y-3">
      {/* Compact Upload Zone - Shopify style */}
      <UploadZone
        allowedTypes={allowedTypes}
        multiple={true}
        onFilesSelected={handleFilesSelected}
        uploads={[]} // Don't show upload list here anymore
      />

      {/* Unified Media Grid - Shopify pattern: optimistic + DB items */}
      <div className="flex-1 overflow-y-auto">
        {error ? (
          <div className="text-center py-12">
            <p className="text-destructive">Failed to load media</p>
            <button
              onClick={() => refetch()}
              className="mt-2 text-sm text-primary hover:underline"
            >
              Try again
            </button>
          </div>
        ) : (
          <MediaGrid
            items={mergedItems}
            selectedIds={selectedIds}
            onToggleSelect={handleToggleSelect}
            onDelete={handleDelete}
            maxSelection={maxSelection}
            loading={loading}
            viewMode={viewMode}
          />
        )}
      </div>
    </div>
  )
}
