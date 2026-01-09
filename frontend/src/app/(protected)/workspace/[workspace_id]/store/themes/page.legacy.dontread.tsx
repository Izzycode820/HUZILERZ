'use client'

import { useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/shadcn-ui/card'
import { Button } from '@/components/shadcn-ui/button'
import { Badge } from '@/components/shadcn-ui/badge'
import { Skeleton } from '@/components/shadcn-ui/skeleton'
import { Paintbrush, Eye, ExternalLink, AlertCircle } from 'lucide-react'
import { useThemeCustomization } from '@/hooks/theme/useThemeCustomization'
import type { WorkspaceThemeListItem } from '@/types/theme/theme-customization'

export default function WorkspaceThemesPage() {
  const params = useParams()
  const router = useRouter()
  const workspaceId = params.workspace_id as string

  const {
    workspaceThemesList,
    isFetchingThemesList,
    error,
    getWorkspaceThemes,
    clearError
  } = useThemeCustomization()

  const themes: WorkspaceThemeListItem[] = workspaceThemesList[workspaceId] || []
  const activeTheme: WorkspaceThemeListItem | undefined = themes.find(t => t.role === 'active') || themes[0]

  useEffect(() => {
    if (workspaceId) {
      getWorkspaceThemes(workspaceId).catch(console.error)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workspaceId])

  const handleCustomize = () => {
    if (activeTheme?.template_id) {
      router.push(`/showcase/editor/${activeTheme.template_id}?workspace=${workspaceId}`)
    }
  }

  const handlePreview = () => {
    if (activeTheme?.preview_url) {
      window.open(activeTheme.preview_url, '_blank')
    }
  }

  // Loading state
  if (isFetchingThemesList) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <Skeleton className="h-8 w-48 mb-2" />
          <Skeleton className="h-4 w-96" />
        </div>

        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-32" />
          </CardHeader>
          <CardContent>
            <div className="grid gap-6 md:grid-cols-2">
              <Skeleton className="h-64 w-full" />
              <div className="space-y-4">
                <Skeleton className="h-6 w-48" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-10 w-32" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <AlertCircle className="h-12 w-12 text-destructive mb-4" />
              <h3 className="text-lg font-semibold mb-2">Failed to Load Themes</h3>
              <p className="text-muted-foreground mb-4">{error.error}</p>
              <Button onClick={() => { clearError(); getWorkspaceThemes(workspaceId) }} variant="outline">
                Try Again
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  // No theme state
  if (!activeTheme) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Paintbrush className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No Theme Assigned</h3>
              <p className="text-muted-foreground mb-4">
                This workspace doesn't have a theme yet. Browse the theme store to get started.
              </p>
              <Button onClick={() => router.push('/showcase')}>
                Browse Themes
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  const getRoleBadgeVariant = (role: string) => {
    switch (role) {
      case 'active':
        return 'default'
      case 'preview':
        return 'secondary'
      case 'unpublished':
        return 'outline'
      default:
        return 'secondary'
    }
  }

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'published':
        return 'default'
      case 'draft':
        return 'secondary'
      default:
        return 'outline'
    }
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Themes</h1>
        <p className="text-muted-foreground">
          Customize your store's appearance and functionality
        </p>
      </div>

      {/* Theme Card - Shopify Style */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Current Theme</CardTitle>
            <div className="flex gap-2">
              <Badge variant={getRoleBadgeVariant(activeTheme.role)} className="capitalize">
                {activeTheme.role}
              </Badge>
              <Badge variant={getStatusBadgeVariant(activeTheme.status)} className="capitalize">
                {activeTheme.status}
              </Badge>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-6 md:grid-cols-[300px_1fr]">
            {/* Theme Preview Image */}
            <div className="relative aspect-[3/4] bg-muted rounded-lg overflow-hidden border">
              <div className="absolute inset-0 flex items-center justify-center">
                <Paintbrush className="h-16 w-16 text-muted-foreground" />
              </div>
              {/* TODO: Add actual preview image when available */}
            </div>

            {/* Theme Details */}
            <div className="space-y-6">
              <div>
                <h2 className="text-2xl font-semibold mb-1">{activeTheme.name}</h2>
                <p className="text-sm text-muted-foreground">
                  {activeTheme.template_name} • ID {activeTheme.template_id}
                </p>
              </div>

              {/* Theme Info */}
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Template Type</p>
                  <p className="text-sm capitalize">{activeTheme.template_type}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Last Updated</p>
                  <p className="text-sm">{activeTheme.updated_at ? new Date(activeTheme.updated_at).toLocaleDateString() : 'N/A'}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Created</p>
                  <p className="text-sm">{activeTheme.created_at ? new Date(activeTheme.created_at).toLocaleDateString() : 'N/A'}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Workspace</p>
                  <p className="text-sm">{activeTheme.workspace_name}</p>
                </div>
              </div>

              {/* Status Info */}
              {activeTheme.has_unpublished_changes && (
                <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4">
                  <p className="text-sm text-yellow-800">
                    You have unpublished changes. Customize and publish to make them live.
                  </p>
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-3 pt-4">
                <Button onClick={handleCustomize} size="lg" className="gap-2">
                  <Paintbrush className="h-4 w-4" />
                  Customize
                </Button>
                <Button onClick={handlePreview} variant="outline" size="lg" className="gap-2">
                  <Eye className="h-4 w-4" />
                  Preview
                </Button>
                {activeTheme.live_url && (
                  <Button
                    variant="ghost"
                    size="lg"
                    className="gap-2"
                    onClick={() => window.open(activeTheme.live_url, '_blank')}
                  >
                    <ExternalLink className="h-4 w-4" />
                    View Live
                  </Button>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Additional Actions Card */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Theme Library</CardTitle>
          <CardDescription>
            Explore more themes to find the perfect look for your store
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button variant="outline" onClick={() => router.push('/showcase')}>
            Browse Theme Store
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
