'use client'

import { UploadZone } from '../UploadZone'
import { useMediaUpload } from '../hooks/useMediaUpload'
import { MediaGrid } from '../MediaGrid'
import type { MediaType, MediaItem } from '../types'
import { useEffect, useRef } from 'react'

interface UploadTabProps {
  allowedTypes?: MediaType[]
  maxSelection?: number
  onUploadsComplete: (items: MediaItem[]) => void
  selectedIds: Set<string>
  onToggleSelect: (uploadId: string, item: MediaItem) => void
}

export function UploadTab({
  allowedTypes,
  maxSelection,
  onUploadsComplete,
  selectedIds,
  onToggleSelect,
}: UploadTabProps) {
  const { uploads, uploadMultiple, clearUploads } = useMediaUpload()

  // Track which items have been reported to prevent duplicates
  const reportedIdsRef = useRef<Set<string>>(new Set())

  // Track completed uploads
  const completedUploads = uploads.filter(
    (u) => u.status === 'completed' && u.result
  )

  // Notify parent when NEW uploads complete (prevent duplicate reports)
  useEffect(() => {
    if (completedUploads.length > 0) {
      const newItems = completedUploads
        .map((u) => u.result)
        .filter((item): item is MediaItem => {
          if (!item) return false
          // Only include items not yet reported
          if (reportedIdsRef.current.has(item.uploadId)) return false
          reportedIdsRef.current.add(item.uploadId)
          return true
        })

      if (newItems.length > 0) {
        onUploadsComplete(newItems)
      }
    }
  }, [completedUploads.length, onUploadsComplete])

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
    const completedItems = completedUploads
      .map((u) => u.result)
      .filter((item): item is MediaItem => item !== null)

    const item = completedItems.find((i) => i.uploadId === uploadId)
    if (item) {
      onToggleSelect(uploadId, item)
    }
  }

  return (
    <div className="space-y-6">
      <UploadZone
        allowedTypes={allowedTypes}
        multiple={true}
        onFilesSelected={handleFilesSelected}
        uploads={uploads}
      />

      {completedUploads.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium">
              Successfully uploaded ({completedUploads.length})
            </p>
            <button
              onClick={handleClear}
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              Clear
            </button>
          </div>

          <MediaGrid
            items={completedUploads
              .map((u) => u.result)
              .filter((item): item is MediaItem => item !== null)}
            selectedIds={selectedIds}
            onToggleSelect={handleToggleSelect}
            selectionEnabled={true}
            maxSelection={maxSelection}
          />
        </div>
      )}
    </div>
  )
}
