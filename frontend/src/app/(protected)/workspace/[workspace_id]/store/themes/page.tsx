'use client';

import React from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useQuery, useMutation } from '@apollo/client/react';
import { ApolloProvider } from '@apollo/client/react';
import { themeClient } from '@/services/graphql/clients';
import { MyThemesDocument } from '@/services/graphql/themes/queries/mythemes/__generated__/myThemes.generated';
import { PublishThemeDocument } from '@/services/graphql/themes/mutations/mythemes/__generated__/publishTheme.generated';
import { DeleteThemeDocument } from '@/services/graphql/themes/mutations/mythemes/__generated__/deleteTheme.generated';
import { DuplicateThemeDocument } from '@/services/graphql/themes/mutations/mythemes/__generated__/duplicateTheme.generated';
import { RenameThemeDocument } from '@/services/graphql/themes/mutations/mythemes/__generated__/renameTheme.generated';
import { ActiveThemeCard } from '@/components/workspace/store/themes/library/ActiveThemeCard';
import { ThemeLibraryCard } from '@/components/workspace/store/themes/library/ThemeLibraryCard';
import { Button } from '@/components/shadcn-ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/shadcn-ui/dialog';
import { Input } from '@/components/shadcn-ui/input';
import { Label } from '@/components/shadcn-ui/label';
import { Eye, Plus, Package } from 'lucide-react';
import { toast } from 'sonner';

function ThemesContent() {
  const params = useParams();
  const router = useRouter();
  const workspaceId = params.workspace_id as string;
  const [publishingThemeId, setPublishingThemeId] = React.useState<string | null>(null);
  const [deletingThemeId, setDeletingThemeId] = React.useState<string | null>(null);
  const [duplicatingThemeId, setDuplicatingThemeId] = React.useState<string | null>(null);
  const [renameDialogOpen, setRenameDialogOpen] = React.useState(false);
  const [renameThemeId, setRenameThemeId] = React.useState<string | null>(null);
  const [renameThemeName, setRenameThemeName] = React.useState('');

  const { data, loading, error, refetch } = useQuery(MyThemesDocument, {
    variables: { workspaceId },
    skip: !workspaceId,
  });

  const [publishTheme] = useMutation(PublishThemeDocument, {
    client: themeClient,
    onCompleted: (data) => {
      setPublishingThemeId(null);
      if (data?.publishTheme?.success) {
        toast.success(data.publishTheme.message || 'Theme published successfully');
        refetch();
      } else if (data?.publishTheme?.error) {
        toast.error(data.publishTheme.error);
      }
    },
    onError: (error) => {
      setPublishingThemeId(null);
      toast.error(`Failed to publish theme: ${error.message}`);
    },
  });

  const [deleteTheme] = useMutation(DeleteThemeDocument, {
    client: themeClient,
    onCompleted: (data) => {
      setDeletingThemeId(null);
      if (data?.deleteTheme?.success) {
        toast.success(data.deleteTheme.message || 'Theme deleted successfully');
        refetch();
      } else if (data?.deleteTheme?.error) {
        toast.error(data.deleteTheme.error);
      }
    },
    onError: (error) => {
      setDeletingThemeId(null);
      toast.error(`Failed to delete theme: ${error.message}`);
    },
  });

  const [duplicateTheme] = useMutation(DuplicateThemeDocument, {
    client: themeClient,
    onCompleted: (data) => {
      setDuplicatingThemeId(null);
      if (data?.duplicateTheme?.success) {
        toast.success(data.duplicateTheme.message || 'Theme duplicated successfully');
        refetch();
      } else if (data?.duplicateTheme?.error) {
        toast.error(data.duplicateTheme.error);
      }
    },
    onError: (error) => {
      setDuplicatingThemeId(null);
      toast.error(`Failed to duplicate theme: ${error.message}`);
    },
  });

  const [renameTheme] = useMutation(RenameThemeDocument, {
    client: themeClient,
    onCompleted: (data) => {
      if (data?.renameTheme?.success) {
        toast.success(data.renameTheme.message || 'Theme renamed successfully');
        refetch();
      } else if (data?.renameTheme?.error) {
        toast.error(data.renameTheme.error);
      }
    },
    onError: (error) => {
      toast.error(`Failed to rename theme: ${error.message}`);
    },
  });

  const handleEditTheme = (customizationId: string) => {
    router.push(`/workspace/${workspaceId}/editor/${customizationId}`);
    //router.push(`/showcase/editor/${customizationId}`);

  };

  const handleViewStore = () => {
    // TODO: Navigate to store preview
    toast.info('Store preview coming soon');
  };

  const handleImportTheme = () => {
    // TODO: Navigate to theme store
    router.push('/showcase');
  };

  const handlePublish = async (customizationId: string) => {
    setPublishingThemeId(customizationId);
    try {
      await publishTheme({
        variables: { id: customizationId },
      });
    } catch (error) {
      // Error already handled in onError callback
      console.error('Error publishing theme:', error);
    }
  };

  const handleDelete = async (customizationId: string) => {
    setDeletingThemeId(customizationId);
    try {
      await deleteTheme({
        variables: { id: customizationId },
      });
    } catch (error) {
      // Error already handled in onError callback
      console.error('Error deleting theme:', error);
    }
  };

  const handleDuplicate = async (customizationId: string, themeName?: string) => {
    setDuplicatingThemeId(customizationId);
    try {
      await duplicateTheme({
        variables: {
          id: customizationId,
          newName: themeName ? `${themeName} (Copy)` : undefined
        },
      });
    } catch (error) {
      // Error already handled in onError callback
      console.error('Error duplicating theme:', error);
    }
  };

  const openRenameDialog = (customizationId: string, currentName: string) => {
    setRenameThemeId(customizationId);
    setRenameThemeName(currentName);
    setRenameDialogOpen(true);
  };

  const handleRenameSubmit = async () => {
    if (!renameThemeId || !renameThemeName.trim()) {
      toast.error('Theme name cannot be empty');
      return;
    }
    try {
      await renameTheme({
        variables: {
          id: renameThemeId,
          name: renameThemeName
        },
      });
      setRenameDialogOpen(false);
      setRenameThemeId(null);
      setRenameThemeName('');
    } catch (error) {
      // Error already handled in onError callback
      console.error('Error renaming theme:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-2">Error loading themes</h2>
          <p className="text-muted-foreground">{error.message}</p>
        </div>
      </div>
    );
  }

  const themes = (data?.myThemes || []).filter((t): t is NonNullable<typeof t> => t !== null);
  const activeTheme = themes.find((t) => t.isActive);
  const libraryThemes = themes.filter((t) => !t.isActive);

  return (
    <div className="w-full max-w-[1000px] mx-auto px-4 sm:px-6">
      <div className="flex flex-col gap-4 sm:gap-6 py-4 sm:py-6">
        {/* Header - stack on mobile */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary rounded-lg flex-shrink-0">
              <Package className="w-5 h-5 text-primary-foreground" />
            </div>
            <h1 className="text-xl sm:text-2xl font-bold">Themes</h1>
          </div>
          <div className="flex items-center gap-2 sm:gap-3">
            <Button variant="outline" onClick={handleViewStore} size="sm" className="flex-1 sm:flex-none">
              <Eye className="w-4 h-4 mr-2" />
              <span className="hidden xs:inline">View your </span>store
            </Button>
            <Button onClick={handleImportTheme} size="sm" className="flex-1 sm:flex-none">
              <Plus className="w-4 h-4 mr-2" />
              Import<span className="hidden xs:inline"> theme</span>
            </Button>
          </div>
        </div>

        {/* Active Theme Section */}
        {activeTheme && (
          <div>
            <ActiveThemeCard
              id={activeTheme.id}
              themeName={activeTheme.themeName}
              previewImage={activeTheme.template.previewImage}
              version={activeTheme.template.version}
              createdAt={activeTheme.createdAt}
              isPasswordProtected={activeTheme.isPasswordProtected}
              storefrontPassword={activeTheme.storefrontPassword}
              onEditTheme={() => handleEditTheme(activeTheme.id)}
              onDuplicate={() => handleDuplicate(activeTheme.id, activeTheme.themeName)}
              onRename={() => openRenameDialog(activeTheme.id, activeTheme.themeName)}
            />
          </div>
        )}

        {/* Theme Library Section */}
        {libraryThemes.length > 0 && (
          <div>
            <div className="mb-4">
              <h2 className="text-base font-semibold">Theme library</h2>
              <p className="text-sm text-muted-foreground mt-1">
                These themes are only visible to you.{' '}
                <span className="text-blue-600 dark:text-blue-400">Publishing a theme from your library</span>{' '}
                will switch it to your current theme.
              </p>
            </div>
            <div className="space-y-3">
              {libraryThemes.map((theme) => (
                <ThemeLibraryCard
                  key={theme.id}
                  id={theme.id}
                  themeName={theme.themeName}
                  previewImage={theme.template.previewImage}
                  version={theme.template.version}
                  createdAt={theme.createdAt}
                  isPublished={theme.isPublished}
                  canDelete={theme.canDelete}
                  isPublishing={publishingThemeId === theme.id}
                  isDuplicating={duplicatingThemeId === theme.id}
                  onEditTheme={() => handleEditTheme(theme.id)}
                  onPublish={() => handlePublish(theme.id)}
                  onDelete={() => handleDelete(theme.id)}
                  onDuplicate={() => handleDuplicate(theme.id, theme.themeName)}
                  onRename={() => openRenameDialog(theme.id, theme.themeName)}
                />
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {themes.length === 0 && (
          <div className="text-center py-16">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-muted/50 mb-4">
              <Package className="w-8 h-8 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-semibold mb-2">No themes yet</h3>
            <p className="text-muted-foreground mb-6">Import a theme from our store to get started</p>
            <Button onClick={handleImportTheme}>
              <Plus className="w-4 h-4 mr-2" />
              Browse themes
            </Button>
          </div>
        )}
      </div>

      {/* Rename Dialog */}
      <Dialog open={renameDialogOpen} onOpenChange={setRenameDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Rename theme</DialogTitle>
            <DialogDescription>
              Enter a new name for your theme
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="theme-name">Theme name</Label>
              <Input
                id="theme-name"
                value={renameThemeName}
                onChange={(e) => setRenameThemeName(e.target.value)}
                placeholder="Enter theme name"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleRenameSubmit();
                  }
                }}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setRenameDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button onClick={handleRenameSubmit}>
              Rename
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default function ThemesPage() {
  return (
    <ApolloProvider client={themeClient}>
      <ThemesContent />
    </ApolloProvider>
  );
}
