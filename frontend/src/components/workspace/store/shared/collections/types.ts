
export interface CollectionSearchModalProps {
    open: boolean
    onOpenChange: (open: boolean) => void
    selectedCollectionIds: string[]
    onAddCollections: (collections: any[]) => void
}
