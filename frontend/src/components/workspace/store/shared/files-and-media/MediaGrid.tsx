'use client'

import { Checkbox } from '@/components/shadcn-ui/checkbox'
import { FileVideo, Box, Trash2 } from 'lucide-react'
import { CircularProgress } from './CircularProgress'
import type { MediaGridProps } from './types'

export function MediaGrid({
  items,
  selectedIds,
  onToggleSelect,
  onDelete,
  selectionEnabled = true,
  maxSelection,
  loading = false,
  viewMode = 'grid',
}: MediaGridProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
        {Array.from({ length: 12 }).map((_, i) => (
          <div
            key={i}
            className="aspect-square bg-muted rounded-md animate-pulse"
          />
        ))}
      </div>
    )
  }

  if (items.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <p>No media files yet</p>
        <p className="text-sm">Upload your first file to get started</p>
      </div>
    )
  }

  // List view
  if (viewMode === 'list') {
    return (
      <div className="space-y-1">
        {items.map((item) => {
          const isSelected = selectedIds.has(item.uploadId)
          const canSelect = !maxSelection || selectedIds.size < maxSelection || isSelected

          return (
            <div
              key={item.uploadId}
              className={`flex items-center gap-3 p-2 rounded-md border cursor-pointer transition-all ${
                isSelected
                  ? 'border-primary bg-primary/5'
                  : 'border-transparent hover:bg-muted'
              }`}
              onClick={() => {
                if (selectionEnabled && canSelect) {
                  onToggleSelect(item.uploadId)
                }
              }}
            >
              {/* Checkbox */}
              {selectionEnabled && (
                <Checkbox checked={isSelected} disabled={!canSelect} />
              )}

              {/* Thumbnail */}
              <div className="w-12 h-12 rounded bg-muted flex-shrink-0 flex items-center justify-center overflow-hidden">
                {item.type === 'image' ? (
                  <img
                    src={item.thumbnailUrl || item.url}
                    alt={item.filename}
                    className="w-full h-full object-cover"
                    loading="lazy"
                  />
                ) : item.type === 'video' ? (
                  item.thumbnailUrl ? (
                    <img
                      src={item.thumbnailUrl}
                      alt={item.filename}
                      className="w-full h-full object-cover"
                      loading="lazy"
                    />
                  ) : (
                    <FileVideo className="h-6 w-6 text-muted-foreground" />
                  )
                ) : (
                  <Box className="h-6 w-6 text-muted-foreground" />
                )}
              </div>

              {/* File Info */}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{item.filename}</p>
                <p className="text-xs text-muted-foreground">
                  {item.type} • {(item.fileSize / 1024).toFixed(1)} KB
                  {item.width && item.height && ` • ${item.width}×${item.height}`}
                </p>
              </div>

              {/* Date */}
              <div className="text-xs text-muted-foreground hidden md:block">
                {new Date(item.uploadedAt).toLocaleDateString()}
              </div>
            </div>
          )
        })}
      </div>
    )
  }

  // Grid view (default) - More columns for compact layout
  return (
    <div className="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
      {items.map((item) => {
        const isSelected = selectedIds.has(item.uploadId)
        const canSelect = !maxSelection || selectedIds.size < maxSelection || isSelected

        return (
          <div
            key={item.uploadId}
            className={`relative group cursor-pointer rounded-md overflow-hidden border-2 transition-all ${
              isSelected
                ? 'border-primary ring-2 ring-primary/20'
                : 'border-transparent hover:border-muted-foreground/30'
            }`}
            onClick={() => {
              if (selectionEnabled && canSelect) {
                onToggleSelect(item.uploadId)
              }
            }}
          >
            {/* Media Preview */}
            <div className="aspect-square bg-muted flex items-center justify-center">
              {item.type === 'image' ? (
                <img
                  src={item.thumbnailUrl || item.url}
                  alt={item.filename}
                  className="w-full h-full object-cover"
                  loading="lazy"
                />
              ) : item.type === 'video' ? (
                <>
                  {item.thumbnailUrl ? (
                    <img
                      src={item.thumbnailUrl}
                      alt={item.filename}
                      className="w-full h-full object-cover"
                      loading="lazy"
                    />
                  ) : (
                    <div className="flex flex-col items-center gap-2 text-muted-foreground">
                      <FileVideo className="h-12 w-12" />
                      <span className="text-xs">Video</span>
                    </div>
                  )}
                </>
              ) : (
                <div className="flex flex-col items-center gap-2 text-muted-foreground">
                  <Box className="h-12 w-12" />
                  <span className="text-xs">3D Model</span>
                </div>
              )}
            </div>

            {/* Checkbox Overlay */}
            {selectionEnabled && (
              <div className="absolute top-2 left-2 z-10">
                <div
                  className={`bg-background/90 rounded-sm ${
                    isSelected ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'
                  } transition-opacity`}
                  onClick={(e) => {
                    e.stopPropagation()
                    if (canSelect) {
                      onToggleSelect(item.uploadId)
                    }
                  }}
                >
                  <Checkbox
                    checked={isSelected}
                    disabled={!canSelect}
                  />
                </div>
              </div>
            )}

            {/* Delete Button - Only show if not uploading */}
            {onDelete && item.status !== 'uploading' && (
              <div className="absolute top-2 right-2 z-10">
                <button
                  className="bg-destructive/90 hover:bg-destructive text-destructive-foreground rounded-sm p-1.5 opacity-0 group-hover:opacity-100 transition-opacity"
                  onClick={(e) => {
                    e.stopPropagation()
                    if (confirm(`Delete "${item.filename}"?`)) {
                      onDelete(item.uploadId)
                    }
                  }}
                  title="Delete"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            )}

            {/* Upload Progress Overlay - Shopify pattern */}
            {item.status === 'uploading' && item.progress !== undefined && (
              <div className="absolute inset-0 bg-black/40 flex items-center justify-center z-20">
                <CircularProgress
                  value={item.progress}
                  size={48}
                  strokeWidth={4}
                  className="drop-shadow-lg"
                />
              </div>
            )}

            {/* Processing Overlay */}
            {item.status === 'processing' && (
              <div className="absolute inset-0 bg-black/40 flex items-center justify-center z-20">
                <div className="text-white text-sm font-medium">
                  Processing...
                </div>
              </div>
            )}

            {/* File Info */}
            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-2 opacity-0 group-hover:opacity-100 transition-opacity">
              <p className="text-xs text-white truncate">{item.filename}</p>
              <p className="text-xs text-white/70">
                {(item.fileSize / 1024).toFixed(1)} KB
              </p>
            </div>
          </div>
        )
      })}
    </div>
  )
}
