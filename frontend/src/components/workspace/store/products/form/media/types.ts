/**
 * Product Media Types
 *
 * Re-exports shared types + product-specific UI state
 */

// Import and re-export shared media types
import type {
  MediaType,
  MediaItem,
  MediaSelection,
} from '@/components/workspace/store/shared/files-and-media'

export type {
  MediaType,
  MediaItem,
  MediaSelection,
}

// Product-specific media state
export interface ProductMediaState {
  /** Media items attached to this product */
  mediaItems: MediaItem[]

  /** IDs to remove (for edit mode) */
  removedIds: string[]
}

export interface ProductMediaSectionProps {
  /** Current media items */
  mediaItems: MediaItem[]

  /** Change handler */
  onChange: (items: MediaItem[]) => void

  /** Existing images from backend (edit mode) */
  existingImages?: Array<{ id: string; url: string; width: number; height: number }>

  /** Remove existing image handler (edit mode) */
  onRemoveExisting?: (uploadId: string) => void
}
