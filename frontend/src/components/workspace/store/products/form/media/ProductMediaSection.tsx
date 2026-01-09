'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/shadcn-ui/card'
import { FilesAndMediaModal } from '@/components/workspace/store/shared/files-and-media'
import { ProductMediaGrid } from './ProductMediaGrid'
import type { ProductMediaSectionProps } from './types'
import type { MediaSelection } from '@/components/workspace/store/shared/files-and-media'

export function ProductMediaSection({
  mediaItems,
  onChange,
  existingImages = [],
  onRemoveExisting,
}: ProductMediaSectionProps) {
  const [showModal, setShowModal] = useState(false)

  const handleMediaSelect = (selection: MediaSelection) => {
    // Combine new and existing uploads
    const allNewItems = [
      ...selection.newUploads,
      ...selection.existingUploads,
    ]

    // Add to current media items
    onChange([...mediaItems, ...allNewItems])
  }

  const handleRemove = (uploadId: string) => {
    // Remove from media items
    onChange(mediaItems.filter((item) => item.uploadId !== uploadId))

    // If it's an existing image, call remove handler
    if (onRemoveExisting) {
      const existingImage = existingImages.find((img) => img.id === uploadId)
      if (existingImage) {
        onRemoveExisting(uploadId)
      }
    }
  }

  const totalMediaCount = mediaItems.length + existingImages.length

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center justify-between">
          <span>Media</span>
          {totalMediaCount > 0 && (
            <span className="text-sm font-normal text-muted-foreground">
              {totalMediaCount} {totalMediaCount === 1 ? 'file' : 'files'}
            </span>
          )}
        </CardTitle>
      </CardHeader>

      <CardContent>
        <ProductMediaGrid
          mediaItems={mediaItems}
          onRemove={handleRemove}
          onAddMore={() => setShowModal(true)}
        />
      </CardContent>

      <FilesAndMediaModal
        open={showModal}
        onClose={() => setShowModal(false)}
        onSelect={handleMediaSelect}
        allowedTypes={['image', 'video', '3d_model']}
        maxSelection={10}
        selectedItems={mediaItems}
      />
    </Card>
  )
}
