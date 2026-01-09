'use client'

import { X, FileVideo, Box, Plus } from 'lucide-react'
import type { MediaItem } from './types'

interface ProductMediaGridProps {
  /** Media items to display */
  mediaItems: MediaItem[]

  /** Remove handler */
  onRemove: (uploadId: string) => void

  /** Add more handler */
  onAddMore: () => void
}

export function ProductMediaGrid({
  mediaItems,
  onRemove,
  onAddMore,
}: ProductMediaGridProps) {
  // Shopify-style: First image is large, rest are smaller
  const [firstImage, ...restImages] = mediaItems

  if (mediaItems.length === 0) {
    // Empty state: Single large dashed box
    return (
      <div
        onClick={onAddMore}
        className="border-2 border-dashed border-muted-foreground/25 rounded-lg hover:border-muted-foreground/40 transition-colors cursor-pointer"
        style={{ aspectRatio: '16 / 10' }}
      >
        <div className="h-full flex flex-col items-center justify-center gap-2 text-muted-foreground">
          <Plus className="h-8 w-8" />
          <p className="text-sm font-medium">Add media</p>
          <p className="text-xs">Images, videos, or 3D models</p>
        </div>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-5 gap-3">
      {/* First Image - Large (spans 3 columns, 2 rows) */}
      <div className="col-span-3 row-span-2 relative group rounded-lg overflow-hidden border">
        <div className="aspect-video bg-muted flex items-center justify-center">
          {firstImage.type === 'image' ? (
            <img
              src={firstImage.optimizedUrl || firstImage.url}
              alt={firstImage.filename}
              className="w-full h-full object-cover"
              loading="lazy"
            />
          ) : firstImage.type === 'video' ? (
            <div className="flex flex-col items-center gap-2 text-muted-foreground">
              <FileVideo className="h-16 w-16" />
              <span className="text-sm">Video</span>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2 text-muted-foreground">
              <Box className="h-16 w-16" />
              <span className="text-sm">3D Model</span>
            </div>
          )}
        </div>

        {/* Remove button */}
        <button
          type="button"
          onClick={() => onRemove(firstImage.uploadId)}
          className="absolute top-2 right-2 bg-destructive text-destructive-foreground rounded-full p-1.5 opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <X className="h-4 w-4" />
        </button>

        {/* Main badge */}
        <div className="absolute bottom-2 left-2 bg-primary text-primary-foreground px-2 py-1 rounded text-xs font-medium">
          Main
        </div>
      </div>

      {/* Dashed Add More Box - Upper right corner (small) */}
      <div
        onClick={onAddMore}
        className="aspect-square border-2 border-dashed border-muted-foreground/25 rounded-lg hover:border-muted-foreground/40 transition-colors cursor-pointer flex items-center justify-center"
      >
        <Plus className="h-6 w-6 text-muted-foreground" />
      </div>

      {/* Rest of images - Small thumbnails */}
      {restImages.slice(0, 9).map((item, index) => (
        <div
          key={item.uploadId}
          className="aspect-square relative group rounded-lg overflow-hidden border"
        >
          <div className="w-full h-full bg-muted flex items-center justify-center">
            {item.type === 'image' ? (
              <img
                src={item.thumbnailUrl || item.url}
                alt={item.filename}
                className="w-full h-full object-cover"
                loading="lazy"
              />
            ) : item.type === 'video' ? (
              <div className="flex flex-col items-center gap-1 text-muted-foreground">
                <FileVideo className="h-6 w-6" />
              </div>
            ) : (
              <div className="flex flex-col items-center gap-1 text-muted-foreground">
                <Box className="h-6 w-6" />
              </div>
            )}
          </div>

          {/* Remove button */}
          <button
            type="button"
            onClick={() => onRemove(item.uploadId)}
            className="absolute top-1 right-1 bg-destructive text-destructive-foreground rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity"
          >
            <X className="h-3 w-3" />
          </button>
        </div>
      ))}

      {/* Show count if more than 10 items */}
      {mediaItems.length > 10 && (
        <div className="aspect-square border rounded-lg flex items-center justify-center bg-muted text-muted-foreground text-sm font-medium">
          +{mediaItems.length - 10}
        </div>
      )}
    </div>
  )
}
