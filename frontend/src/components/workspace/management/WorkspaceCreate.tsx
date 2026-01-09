"use client"

import React, { useState } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft, Loader2 } from 'lucide-react'
import { IconBuildingStore, IconPencil, IconSettings, IconBriefcase } from '@tabler/icons-react'
import { z } from 'zod'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'

// Shadcn/UI Components
import { Button } from '@/components/shadcn-ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/shadcn-ui/card'
import { Input } from '@/components/shadcn-ui/input'
import { Textarea } from '@/components/shadcn-ui/textarea'
import { Alert, AlertDescription } from '@/components/shadcn-ui/alert'

// Custom Components
import { WorkspaceTypeCard } from './WorkspaceTypeCard'
import type { WorkspaceTypeType } from '@/types/workspace/core/workspaceManagement'

// Hooks
import { useWorkspaceManagement } from '@/hooks/workspace/core/useWorkspaceManagement'
import { useAuth } from '@/hooks/authentication/useAuth'

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

// Icon mapping for workspace types
const workspaceTypeIcons: Record<WorkspaceTypeType, React.ComponentType<{ className?: string }>> = {
  store: IconBuildingStore,
  blog: IconPencil,
  services: IconSettings,
  portfolio: IconBriefcase,
}

// Color mapping for workspace types
const workspaceTypeColors: Record<WorkspaceTypeType, string> = {
  store: 'bg-blue-500',
  blog: 'bg-green-500',
  services: 'bg-purple-500',
  portfolio: 'bg-orange-500',
}

// Workspace type configurations
const workspaceTypeConfigs = [
  {
    type: 'store' as WorkspaceTypeType,
    title: 'E-commerce Store',
    description: 'Create an online store to sell products and manage inventory',
    features: ['Product catalog', 'Payment processing', 'Order management', 'Inventory tracking'],
    subscriptionRequired: false
  },
  {
    type: 'blog' as WorkspaceTypeType,
    title: 'Blog',
    description: 'Start a blog to share your thoughts and build an audience',
    features: ['Content management', 'SEO optimization', 'Comment system', 'Analytics'],
    subscriptionRequired: false
  },
  {
    type: 'services' as WorkspaceTypeType,
    title: 'Services',
    description: 'Offer professional services and manage client projects',
    features: ['Service catalog', 'Booking system', 'Client management', 'Project tracking'],
    subscriptionRequired: true
  },
  {
    type: 'portfolio' as WorkspaceTypeType,
    title: 'Portfolio',
    description: 'Showcase your work and build your professional brand',
    features: ['Project gallery', 'Case studies', 'Testimonials', 'Contact forms'],
    subscriptionRequired: false
  }
]

// ============================================================================
// Component Implementation
// ============================================================================

/**
 * Workspace Create Component - Clean Modern Version
 * Multi-step form for workspace creation with proper validation and error handling
 */
export function WorkspaceCreate({ onWorkspaceCreate, className }: WorkspaceCreateProps) {
  const router = useRouter()
  const { createWorkspace, isCreating, error, clearError } = useWorkspaceManagement()
  const { subscription } = useAuth()

  const [step, setStep] = useState<1 | 2>(1)
  const [selectedType, setSelectedType] = useState<WorkspaceTypeType | null>(null)

  const form = useForm<CreateWorkspaceFormValues>({
    resolver: zodResolver(createWorkspaceSchema),
    defaultValues: {
      name: '',
      description: ''
    },
    mode: 'onBlur'
  })

  // Clear errors when form values change
  const watchedValues = form.watch(['name', 'description'])
  React.useEffect(() => {
    if (error) {
      clearError()
    }
  }, [error, clearError, watchedValues])

  const handleTypeSelect = (type: WorkspaceTypeType) => {
    const config = workspaceTypeConfigs.find((c) => c.type === type)

    // Check subscription requirements
    if (config?.subscriptionRequired && subscription?.tier === 'free') {
      // Redirect to upgrade page or show upgrade modal
      router.push('/billing/upgrade?feature=premium-workspace')
      return
    }

    setSelectedType(type)
    setStep(2)
  }

  const handleBackToTypeSelection = () => {
    setStep(1)
    setSelectedType(null)
  }

  const onSubmit = async (data: CreateWorkspaceFormValues) => {
    if (!selectedType) return

    try {
      const response = await createWorkspace({
        name: data.name.trim(),
        type: selectedType,
        description: data.description?.trim() || undefined
      })

      onWorkspaceCreate?.(response)

      // Redirect to workspace listing dashboard
      router.push('/workspace')
    } catch (err) {
      // Error is handled by the hook
      console.error('Failed to create workspace:', err)
    }
  }

  const selectedConfig = selectedType
    ? workspaceTypeConfigs.find((config) => config.type === selectedType)
    : null

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
              Create Workspace
            </h1>
            <p className="text-muted-foreground mt-1">
              {step === 1 ? 'Choose your workspace type' : 'Complete your workspace setup'}
            </p>
          </div>
        </div>

        {/* Progress Indicator */}
        <div className="flex items-center mb-8">
          <div className="flex items-center">
            <div className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium bg-primary text-primary-foreground">
              1
            </div>
            <span className="ml-3 text-sm font-medium text-foreground">
              Type
            </span>
          </div>
          <div className="flex-1 h-px bg-border mx-4" />
          <div className="flex items-center">
            <div className={cn(
              "w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium",
              step >= 2
                ? "bg-primary text-primary-foreground"
                : "bg-muted text-muted-foreground"
            )}>
              2
            </div>
            <span className={cn(
              "ml-3 text-sm font-medium",
              step >= 2
                ? "text-foreground"
                : "text-muted-foreground"
            )}>
              Details
            </span>
          </div>
        </div>

        {/* Step 1: Type Selection */}
        {step === 1 && (
          <div className="max-w-6xl">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {workspaceTypeConfigs.map((config) => (
                <WorkspaceTypeCard
                  key={config.type}
                  type={config.type}
                  title={config.title}
                  description={config.description}
                  features={config.features}
                  isSelected={selectedType === config.type}
                  onSelect={() => handleTypeSelect(config.type)}
                  disabled={config.subscriptionRequired && subscription?.tier === 'free'}
                />
              ))}
            </div>
          </div>
        )}

        {/* Step 2: Details Form */}
        {step === 2 && selectedConfig && selectedType && (
          <div className="max-w-2xl">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className={cn("p-3 rounded-lg text-white", workspaceTypeColors[selectedType])}>
                      {React.createElement(workspaceTypeIcons[selectedType], { className: "w-6 h-6" })}
                    </div>
                    <div>
                      <CardTitle className="text-foreground">
                        {selectedConfig?.title}
                      </CardTitle>
                      <p className="text-sm text-muted-foreground">
                        {selectedConfig?.description}
                      </p>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleBackToTypeSelection}
                  >
                    Change
                  </Button>
                </div>
              </CardHeader>

              <CardContent>
                <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
                  {/* Error Display */}
                  {error && (
                    <Alert variant="destructive">
                      <AlertDescription>
                        {error}
                      </AlertDescription>
                    </Alert>
                  )}

                  {/* Workspace Name */}
                  <div className="space-y-2">
                    <label htmlFor="name" className="text-sm font-medium text-foreground">
                      Workspace Name *
                    </label>
                    <Input
                      id="name"
                      placeholder={`My ${selectedConfig?.title}`}
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
                      placeholder="Tell us about your workspace..."
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

                  {/* Submit Buttons */}
                  <div className="flex justify-between pt-4">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={handleBackToTypeSelection}
                      disabled={isCreating}
                    >
                      Back
                    </Button>
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
        )}
      </div>
    </div>
  )
}

export default WorkspaceCreate