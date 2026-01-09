/**
 * Hook for fetching recent media uploads
 *
 * Uses recentMedia query with generated types
 */

import { useQuery } from '@apollo/client/react'
import type { MediaItem, MediaType } from '../types'
import { RecentMediaDocument } from '@/services/graphql/admin-store/queries/media/__generated__/RecentMedia.generated'
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

interface UseRecentMediaOptions {
  /** Limit number of results */
  limit?: number

  /** Filter by media type */
  mediaType?: MediaType

  /** Search by filename */
  search?: string

  /** Sort by field (date, name, size) */
  sortBy?: 'date' | 'name' | 'size'

  /** Sort order (asc, desc) */
  sortOrder?: 'asc' | 'desc'

  /** Whether to fetch */
  enabled?: boolean
}

export function useRecentMedia(options: UseRecentMediaOptions = {}) {
  const {
    limit = 50,
    mediaType,
    search,
    sortBy = 'date',
    sortOrder = 'desc',
    enabled = true
  } = options

  const { data, loading, error, refetch } = useQuery(RecentMediaDocument, {
    variables: {
      limit,
      mediaType,
      search,
      sortBy,
      sortOrder,
    },
    skip: !enabled,
    fetchPolicy: 'network-only', // Always fetch fresh data for search/filters
  })

  const recentMedia: MediaItem[] =
    data?.recentMedia?.filter((upload): upload is NonNullable<typeof upload> => upload !== null)
      .map((upload) => ({
        uploadId: upload.id,
        url: upload.url || '',
        type: mapMediaType(upload.mediaType),
        filename: upload.originalFilename,
        fileSize: Number(upload.fileSize),
        width: upload.width || undefined,
        height: upload.height || undefined,
        uploadedAt: upload.uploadedAt,
        mimeType: upload.mimeType,
        status: upload.status,
        // Include optimized image URLs (from backend)
        thumbnailUrl: upload.thumbnailUrl || undefined,
        optimizedUrl: upload.optimizedUrl || undefined,
      })) || []

  return {
    recentMedia,
    loading,
    error,
    refetch,
  }
}
