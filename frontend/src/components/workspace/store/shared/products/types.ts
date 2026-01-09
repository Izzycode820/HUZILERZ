export type ProductSearchMode = 'order' | 'collection'

export interface BaseProductSearchModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  selectedProductIds: string[]
}

// Order mode: Multi-product selection with checkboxes (returns full product objects)
export interface OrderModeProps extends BaseProductSearchModalProps {
  mode?: 'order'
  onAddProducts: (products: any[]) => void  // Batch add full product objects
}

// Collection mode: Multiple product selection with checkboxes (returns product IDs)
export interface CollectionModeProps extends BaseProductSearchModalProps {
  mode: 'collection'
  onAddProducts: (productIds: string[]) => void  // Batch add product IDs only
}

export type ProductSearchModalProps = OrderModeProps | CollectionModeProps
