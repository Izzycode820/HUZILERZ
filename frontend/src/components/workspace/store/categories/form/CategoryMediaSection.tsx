'use client'

/**
 * CategoryMediaSection Component
 *
 * Features:
 * - Single image upload for category
 * - Clean Shopify-style UI with dashed border
 * - Simple "Add image" button with drop zone text
 * - Image preview with remove option
 * - Uses existing FilesAndMediaModal
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/shadcn-ui/card'
import { Button } from '@/components/shadcn-ui/button'
import { X } from 'lucide-react'
import { useState } from 'react'
import { FilesAndMediaModal } from '@/components/workspace/store/shared/files-and-media'
import type { MediaItem, MediaSelection } from '@/components/workspace/store/shared/files-and-media'

interface CategoryMediaSectionProps {
  // Media item from upload-first system
  mediaItem?: MediaItem
  onMediaChange: (item?: MediaItem) => void

  // Existing image from backend (optional - for edit mode)
  existingImage?: { id: string; url: string; width: number; height: number }
  onRemoveExisting?: (uploadId: string) => void
}

export function CategoryMediaSection({
  mediaItem,
  onMediaChange,
  existingImage,
  onRemoveExisting
}: CategoryMediaSectionProps) {
  const [showMediaModal, setShowMediaModal] = useState(false)

  const handleMediaSelect = (selection: MediaSelection) => {
    // Get first selected item (single image only)
    const selectedItem = selection.newUploads[0] || selection.existingUploads[0]
    if (selectedItem) {
      onMediaChange(selectedItem)
    }
    setShowMediaModal(false)
  }

  const handleImageRemove = () => {
    // Remove from new uploads
    onMediaChange(undefined)
  }

  const handleExistingImageRemove = () => {
    // Remove existing image from backend
    if (onRemoveExisting && existingImage) {
      onRemoveExisting(existingImage.id)
    }
  }

  // Check if we have any image (existing or new)
  const hasImage = existingImage || mediaItem
  const displayImage = mediaItem ? (mediaItem.thumbnailUrl || mediaItem.url) : existingImage?.url

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base font-semibold">Image</CardTitle>
      </CardHeader>
      <CardContent>
        {/* Image Preview or Upload Area */}
        {hasImage ? (
          <div className="relative group">
            <img
              src={displayImage}
              alt="Category image"
              className="w-full aspect-square rounded-md object-cover border"
            />
            <button
              type="button"
              onClick={mediaItem ? handleImageRemove : handleExistingImageRemove}
              className="absolute -top-2 -right-2 bg-destructive text-destructive-foreground rounded-full p-1.5 opacity-0 group-hover:opacity-100 transition-opacity shadow-md"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        ) : (
          <div className="border-2 border-dashed border-muted-foreground/25 rounded-md p-12 text-center">
            <Button
              type="button"
              variant="outline"
              onClick={() => setShowMediaModal(true)}
              className="mb-2"
            >
              Add image
            </Button>
            <p className="text-xs text-muted-foreground">
              or drop an image to upload
            </p>
          </div>
        )}
      </CardContent>

      {/* Media Modal */}
      <FilesAndMediaModal
        open={showMediaModal}
        onClose={() => setShowMediaModal(false)}
        onSelect={handleMediaSelect}
        allowedTypes={['image']}
        maxSelection={1}
      />
    </Card>
  )
}