/**
 * Files and Media - Shared UI Components
 *
 * Shopify-style media library for workspace
 * Reusable across Products, Categories, and other features
 */

// Main modal
export { FilesAndMediaModal } from './FilesAndMediaModal'

// Components
export { MediaGrid } from './MediaGrid'
export { MediaLibrary } from './MediaLibrary'
export { UploadZone } from './UploadZone'
export { SearchAndFilters } from './SearchAndFilters'
export { ViewModeToggle } from './ViewModeToggle'

// Hooks
export { useMediaUpload } from './hooks/useMediaUpload'
export { useRecentMedia } from './hooks/useRecentMedia'
export { useMediaSelection } from './hooks/useMediaSelection'

// Types
export type {
  MediaType,
  MediaItem,
  MediaSelection,
  MediaModalProps,
  UploadProgress,
  MediaGridProps,
} from './types'
