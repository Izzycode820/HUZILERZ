"use client"

import React from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft, Loader2 } from 'lucide-react'
import { IconBuildingStore } from '@tabler/icons-react'
import { z } from 'zod'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { toast } from 'sonner'

// Shadcn/UI Components
import { Button } from '@/components/shadcn-ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/shadcn-ui/card'
import { Input } from '@/components/shadcn-ui/input'
import { Textarea } from '@/components/shadcn-ui/textarea'

// Hooks
import { useWorkspaceManagement } from '@/hooks/workspace/core/useWorkspaceManagement'

// Utils
import { cn } from '@/lib/utils'

// ============================================================================
// Types and Schemas
// ============================================================================

const createWorkspaceSchema = z.object({
  name: z
    .string()
    .min(1, 'Workspace name is required')
    .max(50, 'Workspace name must be less than 50 characters'),
  description: z
    .string()
    .max(200, 'Description must be less than 200 characters')
    .optional()
})

type CreateWorkspaceFormValues = z.infer<typeof createWorkspaceSchema>

interface WorkspaceCreateProps {
  readonly onWorkspaceCreate?: (workspace: unknown) => void
  readonly className?: string
}

// ============================================================================
// Component Implementation
// ============================================================================

/**
 * Workspace Create Component - Store Only
 * Simplified workspace creation - only supports 'store' type workspaces
 * Shows toast errors and stays on page when creation fails
 */
export function WorkspaceCreate({ onWorkspaceCreate, className }: WorkspaceCreateProps) {
  const router = useRouter()
  const { createWorkspace, isCreating } = useWorkspaceManagement()

  const form = useForm<CreateWorkspaceFormValues>({
    resolver: zodResolver(createWorkspaceSchema),
    defaultValues: {
      name: '',
      description: ''
    },
    mode: 'onBlur'
  })

  const onSubmit = async (data: CreateWorkspaceFormValues) => {
    try {
      const response = await createWorkspace({
        name: data.name.trim(),
        type: 'store', // ✅ Hardcoded - only supporting stores
        description: data.description?.trim() || undefined
      })

      // Success - notify callback and navigate
      onWorkspaceCreate?.(response)
      toast.success('Workspace created successfully!')
      router.push('/workspace')
    } catch (err) {
      // Error - show toast and stay on page (don't navigate)
      const errorMessage = err instanceof Error
        ? err.message
        : 'Failed to create workspace. Please try again.'

      toast.error(errorMessage)
      console.error('Failed to create workspace:', err)
    }
  }

  return (
    <div className={cn('min-h-screen bg-background pt-16', className)}>
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <Button variant="outline" size="sm" onClick={() => router.back()}>
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-foreground">
              Create Store Workspace
            </h1>
            <p className="text-muted-foreground mt-1">
              Set up your online store workspace
            </p>
          </div>
        </div>

        {/* Form */}
        <div className="max-w-2xl">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-lg text-white bg-blue-500">
                  <IconBuildingStore className="w-6 h-6" />
                </div>
                <div>
                  <CardTitle className="text-foreground">
                    E-commerce Store
                  </CardTitle>
                  <p className="text-sm text-muted-foreground">
                    Create an online store to sell products and manage inventory
                  </p>
                </div>
              </div>
            </CardHeader>

            <CardContent>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
                {/* Workspace Name */}
                <div className="space-y-2">
                  <label htmlFor="name" className="text-sm font-medium text-foreground">
                    Workspace Name *
                  </label>
                  <Input
                    id="name"
                    placeholder="My Store"
                    {...form.register('name')}
                    disabled={isCreating}
                  />
                  {form.formState.errors.name && (
                    <p className="text-sm text-destructive">
                      {form.formState.errors.name.message}
                    </p>
                  )}
                </div>

                {/* Description */}
                <div className="space-y-2">
                  <label htmlFor="description" className="text-sm font-medium text-foreground">
                    Description (Optional)
                  </label>
                  <Textarea
                    id="description"
                    placeholder="Tell us about your store..."
                    {...form.register('description')}
                    disabled={isCreating}
                    rows={3}
                  />
                  {form.formState.errors.description && (
                    <p className="text-sm text-destructive">
                      {form.formState.errors.description.message}
                    </p>
                  )}
                </div>

                {/* Submit Button */}
                <div className="flex justify-end pt-4">
                  <Button
                    type="submit"
                    disabled={isCreating || !form.formState.isValid}
                    className="min-w-32"
                  >
                    {isCreating ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Creating...
                      </>
                    ) : (
                      'Create Workspace'
                    )}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

export default WorkspaceCreate