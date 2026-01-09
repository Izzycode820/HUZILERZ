/**
 * Hook for uploading media files with progress tracking
 *
 * Uses uploadMedia mutation with generated types
 */

import { useState, useCallback } from 'react'
import type { MediaItem, UploadProgress } from '../types'
import { useMutation } from '@apollo/client/react'
import { UploadMediaDocument } from '@/services/graphql/admin-store/mutations/media/__generated__/UploadMedia.generated'
import { MedialibMediaUploadMediaTypeChoices } from '@/types/workspace/store/graphql-base'

// Map backend enum to our MediaType
function mapMediaType(backendType: MedialibMediaUploadMediaTypeChoices): 'image' | 'video' | '3d_model' {
  switch (backendType) {
    case MedialibMediaUploadMediaTypeChoices.Image:
      return 'image'
    case MedialibMediaUploadMediaTypeChoices.Video:
      return 'video'
    case MedialibMediaUploadMediaTypeChoices.A_3DModel:
      return '3d_model'
    default:
      return 'image'
  }
}

export function useMediaUpload() {
  const [uploads, setUploads] = useState<Map<string, UploadProgress>>(new Map())
  const [uploadMediaMutation] = useMutation(UploadMediaDocument)

  const uploadFile = useCallback(
    async (file: File): Promise<MediaItem | null> => {
      const uploadId = `temp-${Date.now()}-${file.name}`

      // Create optimistic MediaItem immediately (Shopify pattern)
      const optimisticItem: MediaItem = {
        uploadId,
        url: URL.createObjectURL(file), // Temporary blob URL for preview
        type: file.type.startsWith('image/') ? 'image'
          : file.type.startsWith('video/') ? 'video'
            : '3d_model',
        filename: file.name,
        fileSize: file.size,
        uploadedAt: new Date().toISOString(),
        mimeType: file.type,
        status: 'uploading',
        progress: 0,
        isOptimistic: true,
      }

      // Add optimistic item to progress tracking
      setUploads((prev) => {
        const next = new Map(prev)
        next.set(uploadId, {
          file,
          progress: 0,
          status: 'uploading',
          result: optimisticItem,
        })
        return next
      })

      try {

        // Upload file
        const { data } = await uploadMediaMutation({
          variables: { file },
          context: {
            fetchOptions: {
              useUpload: true,
              onProgress: (ev: ProgressEvent) => {
                if (ev.lengthComputable) {
                  const progress = Math.round((ev.loaded / ev.total) * 100)
                  setUploads((prev) => {
                    const next = new Map(prev)
                    const current = next.get(uploadId)
                    if (current && current.result) {
                      // Update optimistic item progress
                      next.set(uploadId, {
                        ...current,
                        progress,
                        result: { ...current.result, progress }
                      })
                    }
                    return next
                  })
                }
              },
            },
          },
        })

        if (!data?.uploadMedia?.success || !data.uploadMedia.upload) {
          throw new Error(data?.uploadMedia?.error || 'Upload failed')
        }

        const upload = data.uploadMedia.upload

        // Update optimistic item with real data from backend
        const mediaItem: MediaItem = {
          uploadId: upload.id,
          url: upload.url || '',
          type: mapMediaType(upload.mediaType),
          filename: upload.originalFilename,
          fileSize: Number(upload.fileSize),
          width: upload.width || undefined,
          height: upload.height || undefined,
          uploadedAt: upload.uploadedAt,
          mimeType: upload.mimeType,
          status: 'ready', // Shopify pattern: ready to select
          progress: 100,
          isOptimistic: true, // Still optimistic until modal closed
          // Include optimized image URLs (from backend)
          thumbnailUrl: upload.thumbnailUrl || undefined,
          optimizedUrl: upload.optimizedUrl || undefined,
        }

        // Revoke blob URL to free memory
        setUploads((prev) => {
          const next = new Map(prev)
          const current = next.get(uploadId)
          if (current?.result?.url) {
            URL.revokeObjectURL(current.result.url)
          }

          next.set(uploadId, {
            file: current?.file || file,
            status: 'completed',
            progress: 100,
            result: mediaItem,
          })
          return next
        })

        // Don't auto-remove - let user clear manually to allow selection
        return mediaItem
      } catch (error) {
        // Update to error
        setUploads((prev) => {
          const next = new Map(prev)
          const current = next.get(uploadId)
          if (current) {
            next.set(uploadId, {
              ...current,
              status: 'error',
              error: error instanceof Error ? error.message : 'Upload failed',
            })
          }
          return next
        })

        return null
      }
    },
    [uploadMediaMutation]
  )

  const uploadMultiple = useCallback(
    async (files: File[]): Promise<MediaItem[]> => {
      const results = await Promise.all(files.map((file) => uploadFile(file)))
      return results.filter((item): item is MediaItem => item !== null)
    },
    [uploadFile]
  )

  const clearUploads = useCallback(() => {
    setUploads(new Map())
  }, [])

  return {
    uploads: Array.from(uploads.values()),
    uploadFile,
    uploadMultiple,
    clearUploads,
  }
}
