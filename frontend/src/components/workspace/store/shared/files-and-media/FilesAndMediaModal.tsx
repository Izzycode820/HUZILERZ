'use client'

import { useState, useRef } from 'react'
import { ResponsiveModal } from '@/components/shared/responsive-modal'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/shadcn-ui/tabs'
import { Button } from '@/components/shadcn-ui/button'
import { useMediaSelection } from './hooks/useMediaSelection'
import { useIsMobile } from '@/hooks/shadcn/use-mobile'
import { MediaLibrary } from './MediaLibrary'
import { UrlTab } from './tabs/UrlTab'
import { GenerateTab } from './tabs/GenerateTab'
import { SearchAndFilters } from './SearchAndFilters'
import { ViewModeToggle } from './ViewModeToggle'
import type { MediaModalProps, MediaItem } from './types'
import { Link, Sparkles } from 'lucide-react'

export function FilesAndMediaModal({
  open,
  onClose,
  onSelect,
  allowedTypes = ['image', 'video', '3d_model'],
  maxSelection,
  selectedItems = [],
}: MediaModalProps) {
  const [activeTab, setActiveTab] = useState('library')
  const {
    selectedIds,
    toggleSelect,
    clearSelection,
    selectedCount,
  } = useMediaSelection(maxSelection)

  // Search and filter state
  const [search, setSearch] = useState('')
  const [sortBy, setSortBy] = useState<'date' | 'name' | 'size'>('date')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')

  // Track newly uploaded items
  const [newlyUploaded, setNewlyUploaded] = useState<MediaItem[]>([])

  // Track items selected from library
  const [librarySelected, setLibrarySelected] = useState<MediaItem[]>([])

  // Store clearUploads function from MediaLibrary (Shopify pattern)
  const clearUploadsRef = useRef<(() => void) | null>(null)
  const handleClearUploads = (clearFn: () => void) => {
    clearUploadsRef.current = clearFn
  }

  // Auto-select newly uploaded items
  const handleUploadsComplete = (items: MediaItem[]) => {
    setNewlyUploaded((prev) => [...prev, ...items])
    items.forEach((item) => {
      if (!selectedIds.has(item.uploadId)) {
        toggleSelect(item.uploadId)
      }
    })
  }

  // Handle URL upload complete
  const handleUrlUploadComplete = (item: MediaItem) => {
    handleUploadsComplete([item])
  }

  // Handle selection from library
  const handleLibrarySelect = (uploadId: string, item: MediaItem) => {
    toggleSelect(uploadId)

    // Add or remove from librarySelected
    setLibrarySelected((prev) => {
      const exists = prev.some((i) => i.uploadId === uploadId)
      if (exists) {
        return prev.filter((i) => i.uploadId !== uploadId)
      } else {
        return [...prev, item]
      }
    })
  }

  // Handle selection confirmation
  const handleConfirm = () => {
    // Get selected items: newly uploaded + items from library
    const selectedNewUploads = newlyUploaded.filter((item) =>
      selectedIds.has(item.uploadId)
    )
    const selectedLibraryItems = librarySelected.filter((item) =>
      selectedIds.has(item.uploadId)
    )

    onSelect({
      newUploads: selectedNewUploads,
      existingUploads: selectedLibraryItems,
    })

    // Reset state
    clearSelection()
    setNewlyUploaded([])
    setLibrarySelected([])
    setSearch('')
    onClose()
  }

  // Handle cancel - Clear optimistic uploads (Shopify pattern)
  const handleCancel = () => {
    clearSelection()
    setNewlyUploaded([])
    setLibrarySelected([])
    setSearch('')

    // Clear optimistic uploads on modal close
    if (clearUploadsRef.current) {
      clearUploadsRef.current()
    }

    onClose()
  }

  const isMobile = useIsMobile()

  // Footer content - shared between mobile and desktop
  const footerContent = (
    <div className="flex w-full items-center justify-between">
      <div className="text-sm text-muted-foreground">
        {selectedCount > 0 && (
          <span>
            {selectedCount} selected
            {maxSelection && ` (max ${maxSelection})`}
          </span>
        )}
      </div>
      <div className="flex gap-2">
        <Button variant="outline" onClick={handleCancel}>
          Cancel
        </Button>
        <Button onClick={handleConfirm} disabled={selectedCount === 0}>
          Done
        </Button>
      </div>
    </div>
  )

  return (
    <ResponsiveModal
      open={open}
      onClose={handleCancel}
      title="Select files"
      dialogClassName="max-w-[95vw] w-[1000px] h-[85vh] max-h-[900px] flex flex-col"
      footer={footerContent}
    >
      {/* Main Content Area */}
      <div className="flex-1 flex gap-6 min-h-0 overflow-hidden md:px-6 px-4 py-4">
        {/* Left Side: Main Content */}
        <div className="flex-1 flex flex-col min-h-0">
          {/* Top Bar: View Mode (left) and Tabs (center) */}
          <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
            {!isMobile && <ViewModeToggle viewMode={viewMode} onViewModeChange={setViewMode} />}

            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="flex-wrap h-auto">
                <TabsTrigger value="library" className="text-xs md:text-sm">
                  {isMobile ? 'Library' : 'Media Library'}
                </TabsTrigger>
                <TabsTrigger value="url" className="flex items-center gap-1 md:gap-2 text-xs md:text-sm">
                  <Link className="h-3 w-3 md:h-4 md:w-4" />
                  URL
                </TabsTrigger>
                <TabsTrigger value="generate" className="flex items-center gap-1 md:gap-2 text-xs md:text-sm">
                  <Sparkles className="h-3 w-3 md:h-4 md:w-4" />
                  {isMobile ? 'AI' : 'AI Generate'}
                </TabsTrigger>
              </TabsList>
            </Tabs>

            {!isMobile && <div className="w-[140px]" />} {/* Spacer for balance */}
          </div>

          {/* Mobile: Search input inline */}
          {isMobile && (
            <div className="mb-3">
              <SearchAndFilters
                search={search}
                onSearchChange={setSearch}
                sortBy={sortBy}
                onSortByChange={setSortBy}
                sortOrder={sortOrder}
                onSortOrderChange={setSortOrder}
                compact
              />
            </div>
          )}

          {/* Tab Content */}
          <div className="flex-1 overflow-hidden">
            <Tabs value={activeTab} className="h-full flex flex-col">
              <TabsContent value="library" className="flex-1 mt-0 overflow-hidden">
                <MediaLibrary
                  selectedIds={selectedIds}
                  onToggleSelect={handleLibrarySelect}
                  allowedTypes={allowedTypes}
                  maxSelection={maxSelection}
                  search={search}
                  sortBy={sortBy}
                  sortOrder={sortOrder}
                  viewMode={isMobile ? 'grid' : viewMode}
                  onUploadsComplete={handleUploadsComplete}
                  onClearUploads={handleClearUploads}
                />
              </TabsContent>

              <TabsContent value="url" className="flex-1 mt-0 overflow-auto">
                <UrlTab onUploadComplete={handleUrlUploadComplete} />
              </TabsContent>

              <TabsContent value="generate" className="flex-1 mt-0 overflow-auto">
                <GenerateTab />
              </TabsContent>
            </Tabs>
          </div>
        </div>

        {/* Right Sidebar: Search & Filters - Desktop only */}
        {!isMobile && (
          <div className="w-64 flex-shrink-0 border-l pl-6">
            <SearchAndFilters
              search={search}
              onSearchChange={setSearch}
              sortBy={sortBy}
              onSortByChange={setSortBy}
              sortOrder={sortOrder}
              onSortOrderChange={setSortOrder}
            />
          </div>
        )}
      </div>
    </ResponsiveModal>
  )
}
