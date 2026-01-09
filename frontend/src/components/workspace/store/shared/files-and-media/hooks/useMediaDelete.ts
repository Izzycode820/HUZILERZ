/**
 * Hook for deleting media files
 *
 * Uses deleteMedia mutation with generated types
 */

import { useCallback } from 'react'
import { useMutation } from '@apollo/client/react'
import { DeleteMediaDocument } from '@/services/graphql/admin-store/mutations/media/__generated__/DeleteMedia.generated'

export function useMediaDelete(onDeleteSuccess?: () => void) {
  const [deleteMediaMutation, { loading }] = useMutation(DeleteMediaDocument)

  const deleteMedia = useCallback(
    async (uploadId: string): Promise<boolean> => {
      try {
        const { data } = await deleteMediaMutation({
          variables: { uploadId },
        })

        if (!data?.deleteMedia?.success) {
          throw new Error(data?.deleteMedia?.error || 'Delete failed')
        }

        // Trigger refetch callback if provided
        if (onDeleteSuccess) {
          onDeleteSuccess()
        }

        return true
      } catch (error) {
        console.error('Delete media failed:', error)
        return false
      }
    },
    [deleteMediaMutation, onDeleteSuccess]
  )

  return {
    deleteMedia,
    deleting: loading,
  }
}
