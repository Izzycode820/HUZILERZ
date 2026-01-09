'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useMutation } from '@apollo/client/react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/shadcn-ui/dialog'
import { Button } from '@/components/shadcn-ui/button'
import { RadioGroup, RadioGroupItem } from '@/components/shadcn-ui/radio-group'
import { Label } from '@/components/shadcn-ui/label'
import { Badge } from '@/components/shadcn-ui/badge'
import { Loader2, Briefcase, Building2, ShoppingBag, Layers } from 'lucide-react'
import { useWorkspaceManagement } from '@/hooks/workspace/core/useWorkspaceManagement'
import { useWorkspace } from '@/hooks/authentication/useWorkspace'
import { AddThemeDocument } from '@/services/graphql/themes/mutations/mythemes/__generated__/addTheme.generated'
import { toast } from 'sonner'

interface WorkspaceSelectionModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  themeSlug: string
  themeName: string
}

const workspaceTypeIcons = {
  ecommerce: ShoppingBag,
  portfolio: Briefcase,
  saas: Building2,
  default: Layers,
} as const

export function WorkspaceSelectionModal({
  open,
  onOpenChange,
  themeSlug,
  themeName,
}: WorkspaceSelectionModalProps) {
  const router = useRouter()

  // Hooks
  const { workspaces, isLoading, error, listWorkspaces } = useWorkspaceManagement()
  const { switchWorkspace, isSwitching } = useWorkspace()

  // GraphQL Mutation
  const [addTheme, { loading: isAddingTheme }] = useMutation(AddThemeDocument)

  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState<string>('')

  const activeWorkspaces = workspaces.filter((ws) => ws.status === 'active')

  // Fetch workspaces when modal opens
  useEffect(() => {
    if (open) {
      listWorkspaces()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open])

  const handleContinue = async () => {
    if (!selectedWorkspaceId) {
      toast.error('Please select a workspace')
      return
    }

    try {
      // Step 1: FIRST switch workspace context (updates Zustand store + localStorage)
      // This ensures X-Workspace-Id header is set for subsequent GraphQL calls
      await switchWorkspace(selectedWorkspaceId)

      // Small delay to ensure store propagation (React state update)
      await new Promise(resolve => setTimeout(resolve, 100))

      // Step 2: NOW add theme (authLink will read workspace from store)
      const { data } = await addTheme({
        variables: {
          workspaceId: selectedWorkspaceId,
          themeSlug: themeSlug,
        },
      })

      if (data?.addTheme?.error) {
        toast.error(data.addTheme.error)
        return
      }

      if (!data?.addTheme?.success) {
        toast.error('Failed to add theme')
        return
      }

      toast.success('Theme added successfully!')

      // Close modal
      onOpenChange(false)

      // Step 3: Navigate to themes library
      router.push(`/workspace/${selectedWorkspaceId}/store/themes`)
    } catch (error: any) {
      console.error('Failed to add theme:', error)
      toast.error('Failed to add theme. Please try again.')
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Assign Theme to Workspace</DialogTitle>
          <DialogDescription>
            Choose which workspace you'd like to use{' '}
            <span className="font-medium text-foreground">{themeName}</span> in.
          </DialogDescription>
        </DialogHeader>

        <div className="py-6">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : activeWorkspaces.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-sm text-muted-foreground">No active workspaces found.</p>
              <Button variant="link" size="sm" className="mt-2">
                Create a workspace
              </Button>
            </div>
          ) : (
            <RadioGroup value={selectedWorkspaceId} onValueChange={setSelectedWorkspaceId}>
              <div className="space-y-3 max-h-[300px] overflow-y-auto pr-2">
                {activeWorkspaces.map((workspace) => {
                  const Icon =
                    workspaceTypeIcons[workspace.type as keyof typeof workspaceTypeIcons] ||
                    workspaceTypeIcons.default

                  return (
                    <div
                      key={workspace.id}
                      className={`
                        relative flex items-start space-x-3 rounded-lg border p-4 cursor-pointer
                        transition-colors hover:bg-accent/50
                        ${selectedWorkspaceId === workspace.id
                          ? 'border-primary bg-accent/50'
                          : 'border-border'
                        }
                      `}
                      onClick={() => setSelectedWorkspaceId(workspace.id)}
                    >
                      <RadioGroupItem value={workspace.id} id={workspace.id} className="mt-0.5" />
                      <div className="flex-1 min-w-0">
                        <Label
                          htmlFor={workspace.id}
                          className="flex items-center gap-2 font-medium cursor-pointer"
                        >
                          <Icon className="h-4 w-4 text-muted-foreground" />
                          <span className="truncate">{workspace.name}</span>
                        </Label>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge variant="secondary" className="text-xs capitalize">
                            {workspace.type}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </RadioGroup>
          )}
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isAddingTheme || isSwitching}
          >
            Cancel
          </Button>
          <Button
            onClick={handleContinue}
            disabled={!selectedWorkspaceId || isAddingTheme || isSwitching}
          >
            {isAddingTheme || isSwitching ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                {isAddingTheme ? 'Adding theme...' : 'Switching workspace...'}
              </>
            ) : (
              'Continue'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
