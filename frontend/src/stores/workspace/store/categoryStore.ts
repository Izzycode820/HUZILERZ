/**
 * Category Store - Store category management
 * Zustand 2024 Best Practices
 * Manages store category CRUD operations and state
 */

import { create } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'
import { immer } from 'zustand/middleware/immer'
import type {
  Category,
  CategoryListItem,
  CreateCategoryRequest,
  UpdateCategoryRequest,
  CategoryListResponse,
  CategoryDetailResponse,
  CategoryCreateResponse,
  CategoryUpdateResponse,
  CategoryTreeResponse
} from '../../../types/workspace/store'
import { createCategoryService } from '../../../services/workspace/store/category'

// ============================================================================
// Category Store State Interface
// ============================================================================

interface CategoryStoreState {
  // Category Data
  categories: CategoryListItem[]
  categoryDetails: Record<string, Category> // Cache for individual categories
  categoryTree: Category[]

  // UI State
  isLoading: boolean
  isCreating: boolean
  isUpdating: boolean
  isDeleting: boolean
  error: string | null

  // Actions - Category Management
  listCategories: (workspaceId: string, force?: boolean) => Promise<void>
  getCategory: (workspaceId: string, categoryId: string) => Promise<void>
  createCategory: (workspaceId: string, request: CreateCategoryRequest) => Promise<CategoryCreateResponse>
  updateCategory: (workspaceId: string, categoryId: string, request: UpdateCategoryRequest) => Promise<CategoryUpdateResponse>
  deleteCategory: (workspaceId: string, categoryId: string) => Promise<CategoryDetailResponse>
  getCategoryTree: (workspaceId: string) => Promise<void>

  // UI Actions
  setLoading: (loading: boolean) => void
  setCreating: (creating: boolean) => void
  setUpdating: (updating: boolean) => void
  setDeleting: (deleting: boolean) => void
  setError: (error: string | null) => void
  clearError: () => void
  clearCategories: () => void

  // Helper Methods
  hasCategories: () => boolean
  getCategoryById: (categoryId: string) => Category | undefined
  getRootCategories: () => CategoryListItem[]
  getSubcategories: (parentId: string) => CategoryListItem[]
  isRootCategory: (categoryId: string) => boolean
  hasSubcategories: (categoryId: string) => boolean
}

// ============================================================================
// Create Category Store
// ============================================================================

export const useCategoryStore = create<CategoryStoreState>()(
  subscribeWithSelector(
    immer((set, get) => ({
      // ========================================================================
      // Initial State
      // ========================================================================
      categories: [],
      categoryDetails: {},
      categoryTree: [],
      isLoading: false,
      isCreating: false,
      isUpdating: false,
      isDeleting: false,
      error: null,

      // ========================================================================
      // Category Actions
      // ========================================================================

      listCategories: async (workspaceId, force = false) => {
        if (!workspaceId) {
          throw new Error('Workspace ID is required')
        }

        // Skip if already loading or data exists (prevents infinite loops)
        const { isLoading, categories } = get()
        if (isLoading) return
        if (!force && categories.length > 0) return

        set((state) => {
          state.isLoading = true
          state.error = null
        })

        try {
          const categoryService = createCategoryService(workspaceId)
          const response = await categoryService.listCategories()

          set((state) => {
            if (response.success && response.data) {
              state.categories = [...response.data]
            }
            state.isLoading = false
          })
        } catch (error) {
          set((state) => {
            state.error = error instanceof Error ? error.message : 'Failed to fetch categories'
            state.isLoading = false
          })
          throw error
        }
      },

      getCategory: async (workspaceId, categoryId) => {
        if (!workspaceId) {
          throw new Error('Workspace ID is required')
        }
        if (!categoryId) {
          throw new Error('Category ID is required')
        }

        set((state) => {
          state.isLoading = true
          state.error = null
        })

        try {
          const categoryService = createCategoryService(workspaceId)
          const response = await categoryService.getCategory(categoryId)

          set((state) => {
            if (response.success && response.data) {
              state.categoryDetails[categoryId] = {
                ...response.data,
                breadcrumb_path: [...response.data.breadcrumb_path]
              }
            }
            state.isLoading = false
          })
        } catch (error) {
          set((state) => {
            state.error = error instanceof Error ? error.message : 'Failed to fetch category'
            state.isLoading = false
          })
          throw error
        }
      },

      createCategory: async (workspaceId, request) => {
        if (!workspaceId) {
          throw new Error('Workspace ID is required')
        }

        set((state) => {
          state.isCreating = true
          state.error = null
        })

        try {
          const categoryService = createCategoryService(workspaceId)
          const response = await categoryService.createCategory(request)

          set((state) => {
            if (response.success && response.data) {
              // Add new category to the list
              state.categories.push(response.data)
              // Cache the category details
              state.categoryDetails[response.data.id] = {
                ...response.data,
                breadcrumb_path: [...response.data.breadcrumb_path]
              }
            }
            state.isCreating = false
          })

          return response
        } catch (error) {
          set((state) => {
            state.error = error instanceof Error ? error.message : 'Failed to create category'
            state.isCreating = false
          })
          throw error
        }
      },

      updateCategory: async (workspaceId, categoryId, request) => {
        if (!workspaceId) {
          throw new Error('Workspace ID is required')
        }
        if (!categoryId) {
          throw new Error('Category ID is required')
        }

        set((state) => {
          state.isUpdating = true
          state.error = null
        })

        try {
          const categoryService = createCategoryService(workspaceId)
          const response = await categoryService.updateCategory(categoryId, request)

          set((state) => {
            if (response.success && response.data) {
              // Update category in list
              const categoryIndex = state.categories.findIndex(cat => cat.id === categoryId)
              if (categoryIndex !== -1) {
                state.categories[categoryIndex] = { ...state.categories[categoryIndex], ...response.data }
              }

              // Update category in details cache
              if (state.categoryDetails[categoryId]) {
                state.categoryDetails[categoryId] = {
                  ...state.categoryDetails[categoryId],
                  ...response.data,
                  breadcrumb_path: response.data.breadcrumb_path ? [...response.data.breadcrumb_path] : state.categoryDetails[categoryId].breadcrumb_path
                }
              }
            }
            state.isUpdating = false
          })

          return response
        } catch (error) {
          set((state) => {
            state.error = error instanceof Error ? error.message : 'Failed to update category'
            state.isUpdating = false
          })
          throw error
        }
      },

      deleteCategory: async (workspaceId, categoryId) => {
        if (!workspaceId) {
          throw new Error('Workspace ID is required')
        }
        if (!categoryId) {
          throw new Error('Category ID is required')
        }

        set((state) => {
          state.isDeleting = true
          state.error = null
        })

        try {
          const categoryService = createCategoryService(workspaceId)
          const response = await categoryService.deleteCategory(categoryId)

          set((state) => {
            // Remove category from list
            state.categories = state.categories.filter(cat => cat.id !== categoryId)

            // Remove category from details cache
            delete state.categoryDetails[categoryId]

            state.isDeleting = false
          })

          return response
        } catch (error) {
          set((state) => {
            state.error = error instanceof Error ? error.message : 'Failed to delete category'
            state.isDeleting = false
          })
          throw error
        }
      },

      getCategoryTree: async (workspaceId) => {
        if (!workspaceId) {
          throw new Error('Workspace ID is required')
        }

        set((state) => {
          state.isLoading = true
          state.error = null
        })

        try {
          const categoryService = createCategoryService(workspaceId)
          const response = await categoryService.getCategoryTree()

          set((state) => {
            if (response.success && response.data) {
              state.categoryTree = response.data.map(category => ({
                ...category,
                breadcrumb_path: [...category.breadcrumb_path]
              }))
            }
            state.isLoading = false
          })
        } catch (error) {
          set((state) => {
            state.error = error instanceof Error ? error.message : 'Failed to fetch category tree'
            state.isLoading = false
          })
          throw error
        }
      },

      // ========================================================================
      // UI State Actions
      // ========================================================================

      setLoading: (loading) => {
        set((state) => {
          state.isLoading = loading
        })
      },

      setCreating: (creating) => {
        set((state) => {
          state.isCreating = creating
        })
      },

      setUpdating: (updating) => {
        set((state) => {
          state.isUpdating = updating
        })
      },

      setDeleting: (deleting) => {
        set((state) => {
          state.isDeleting = deleting
        })
      },

      setError: (error) => {
        set((state) => {
          state.error = error
          if (error) {
            state.isLoading = false
            state.isCreating = false
            state.isUpdating = false
            state.isDeleting = false
          }
        })
      },

      clearError: () => {
        set((state) => {
          state.error = null
        })
      },

      clearCategories: () => {
        set((state) => {
          state.categories = []
          state.categoryDetails = {}
          state.categoryTree = []
          state.error = null
        })
      },

      // ========================================================================
      // Helper Methods
      // ========================================================================

      hasCategories: () => {
        const { categories } = get()
        return categories.length > 0
      },

      getCategoryById: (categoryId) => {
        const { categoryDetails, categories } = get()

        // Check cache first
        if (categoryDetails[categoryId]) {
          return categoryDetails[categoryId]
        }

        // Fallback to list
        const category = categories.find(cat => cat.id === categoryId)
        if (category) {
          // Convert list item to full category data
          return {
            id: category.id,
            name: category.name,
            description: category.description,
            slug: category.slug,
            parent: category.parent,
            image: '',
            sort_order: 0,
            is_visible: category.is_visible,
            is_featured: category.is_featured,
            meta_title: '',
            meta_description: '',
            meta_keywords: '',
            category_type: 'main',
            attributes: category.attributes,
            product_count: category.product_count,
            total_products: category.total_products,
            average_price: category.average_price,
            level: category.level,
            is_root_category: category.is_root_category,
            has_children: category.has_children,
            breadcrumb_path: [],
            active_product_count: 0,
            all_product_count: 0,
            created_at: '',
            updated_at: ''
          }
        }

        return undefined
      },

      getRootCategories: () => {
        const { categories } = get()
        return categories.filter(cat => cat.is_root_category)
      },

      getSubcategories: (parentId) => {
        const { categories } = get()
        return categories.filter(cat => cat.parent === parentId)
      },

      isRootCategory: (categoryId) => {
        const category = get().getCategoryById(categoryId)
        return category?.is_root_category ?? false
      },

      hasSubcategories: (categoryId) => {
        const { categories } = get()
        return categories.some(cat => cat.parent === categoryId)
      }
    }))
  )
)

// ============================================================================
// Selectors for Performance
// ============================================================================

export const categorySelectors = {
  // Core selectors
  categories: (state: CategoryStoreState) => state.categories,
  categoryTree: (state: CategoryStoreState) => state.categoryTree,
  isLoading: (state: CategoryStoreState) => state.isLoading,
  isCreating: (state: CategoryStoreState) => state.isCreating,
  isUpdating: (state: CategoryStoreState) => state.isUpdating,
  isDeleting: (state: CategoryStoreState) => state.isDeleting,
  error: (state: CategoryStoreState) => state.error,

  // Computed selectors
  hasCategories: (state: CategoryStoreState) => state.categories.length > 0,
  categoryCount: (state: CategoryStoreState) => state.categories.length,
  rootCategories: (state: CategoryStoreState) => state.categories.filter(cat => cat.is_root_category),
  featuredCategories: (state: CategoryStoreState) => state.categories.filter(cat => cat.is_featured),
  visibleCategories: (state: CategoryStoreState) => state.categories.filter(cat => cat.is_visible),

  // Action selectors (stable references)
  listCategories: (state: CategoryStoreState) => state.listCategories,
  getCategory: (state: CategoryStoreState) => state.getCategory,
  createCategory: (state: CategoryStoreState) => state.createCategory,
  updateCategory: (state: CategoryStoreState) => state.updateCategory,
  deleteCategory: (state: CategoryStoreState) => state.deleteCategory,
  getCategoryTree: (state: CategoryStoreState) => state.getCategoryTree,
  clearError: (state: CategoryStoreState) => state.clearError,
  clearCategories: (state: CategoryStoreState) => state.clearCategories,

  // Helper method selectors
  getCategoryById: (state: CategoryStoreState) => state.getCategoryById,
  getRootCategories: (state: CategoryStoreState) => state.getRootCategories,
  getSubcategories: (state: CategoryStoreState) => state.getSubcategories,
  isRootCategory: (state: CategoryStoreState) => state.isRootCategory,
  hasSubcategories: (state: CategoryStoreState) => state.hasSubcategories,
}

// ============================================================================
// Default Export
// ============================================================================

export default useCategoryStore