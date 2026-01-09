/**
 * Shared types for Files and Media system
 *
 * Used across:
 * - Products
 * - Categories
 * - Any feature requiring media upload
 */

export type MediaType = 'image' | 'video' | '3d_model'

export interface MediaItem {
  /** Upload ID from backend */
  uploadId: string

  /** Original file URL */
  url: string

  /** Media type */
  type: MediaType

  /** Original filename */
  filename: string

  /** File size in bytes */
  fileSize: number

  /** Image/video dimensions (optional) */
  width?: number
  height?: number

  /** Upload timestamp */
  uploadedAt: string

  /** MIME type */
  mimeType: string

  /** Processing status - Shopify pattern: uploading, processing, ready */
  status?: 'uploading' | 'processing' | 'ready' | string

  /** Upload progress 0-100 (for uploading items) */
  progress?: number

  /** Is this an optimistic item (new upload not yet in DB)? */
  isOptimistic?: boolean

  // Optimized image versions (images only)
  /** Thumbnail URL (for images/videos) */
  thumbnailUrl?: string
  /** Optimized version URL (for images) */
  optimizedUrl?: string
}

export interface MediaSelection {
  /** Newly uploaded items (just uploaded in modal) */
  newUploads: MediaItem[]

  /** Existing items selected from recent */
  existingUploads: MediaItem[]
}

export interface MediaModalProps {
  /** Whether modal is open */
  open: boolean

  /** Close handler */
  onClose: () => void

  /** Selection handler */
  onSelect: (selection: MediaSelection) => void

  /** Allowed media types */
  allowedTypes?: MediaType[]

  /** Maximum number of items to select */
  maxSelection?: number

  /** Already selected items (to show as selected in recent) */
  selectedItems?: MediaItem[]
}

export interface UploadProgress {
  /** File being uploaded */
  file: File

  /** Upload progress (0-100) */
  progress: number

  /** Upload status */
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'error'

  /** Error message if failed */
  error?: string

  /** Result if completed */
  result?: MediaItem
}

export interface MediaGridProps {
  /** Media items to display */
  items: MediaItem[]

  /** Selected item IDs */
  selectedIds: Set<string>

  /** Selection handler */
  onToggleSelect: (uploadId: string) => void

  /** Delete handler (optional) */
  onDelete?: (uploadId: string) => void

  /** Whether selection is enabled */
  selectionEnabled?: boolean

  /** Maximum selection */
  maxSelection?: number

  /** Loading state */
  loading?: boolean

  /** View mode */
  viewMode?: 'grid' | 'list'
}
