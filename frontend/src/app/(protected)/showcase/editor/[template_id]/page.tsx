'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { Editor } from '@/puck-visual-designer/puck';
import { useThemeManifest } from '@/hooks/theme';
import themeCustomizationService from '@/services/theme/theme.customization';
import type { Data } from '@measured/puck';
import { toast } from 'sonner';

/**
 * Template editor page that works with any template configuration.
 * Supports workspace-specific customization via ?workspace= query param.
 */
export default function TemplateEditorPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const templateId = params.template_id as string;
  const workspaceId = searchParams.get('workspace'); // Check for workspace context

  const {
    currentTheme,
    isLoading,
    error,
    loadThemeWithFallback,
    clearError
  } = useThemeManifest();

  const [saving, setSaving] = useState(false);
  const [workspaceTheme, setWorkspaceTheme] = useState<any>(null);
  const [isLoadingWorkspace, setIsLoadingWorkspace] = useState(false);

  // Silent auto-save - refs for debouncing and cleanup
  const autoSaveTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const lastDataRef = useRef<Data | null>(null);

  const loadTemplateData = useCallback(async () => {
    console.log('🔵 [EditorPage] loadTemplateData started', { templateId, workspaceId });
    try {
      clearError();

      if (!templateId) {
        console.log('⚠️ [EditorPage] No templateId, aborting');
        return;
      }

      // Check if this is workspace-specific editing
      if (workspaceId) {
        console.log('🔵 [EditorPage] Loading workspace theme for:', workspaceId);
        setIsLoadingWorkspace(true);

        // Load workspace theme customization
        const response = await themeCustomizationService.getWorkspaceTheme(workspaceId);
        console.log('✅ [EditorPage] Workspace theme response:', response);

        if (response.success) {
          setWorkspaceTheme(response.data);
          console.log('✅ [EditorPage] Workspace theme set');
        } else {
          console.error('❌ [EditorPage] Failed to load workspace theme:', response.message);
          toast.error('Failed to load workspace theme');
        }

        setIsLoadingWorkspace(false);
      }

      if (!workspaceId) {
        console.error('❌ [EditorPage] No workspace ID!');
        throw new Error('Workspace ID required');
      }

      console.log('🔵 [EditorPage] Calling loadThemeWithFallback...');
      await loadThemeWithFallback(workspaceId);
      console.log('✅ [EditorPage] loadThemeWithFallback completed');

    } catch (error) {
      console.error('❌ [EditorPage] Template loading failed:', error);
      setIsLoadingWorkspace(false);
    }
  }, [templateId, workspaceId, clearError, loadThemeWithFallback]);

  useEffect(() => {
    if (templateId && templateId !== 'blank-canvas') {
      loadTemplateData();
    }
  }, [templateId, loadTemplateData]);

  const handlePublish = async (data: Data) => {
    try {
      setSaving(true);

      if (!workspaceId) {
        toast.error('No workspace selected. Please select a workspace first.');
        return;
      }

      // Save to workspace customization
      const response = await themeCustomizationService.updateWorkspaceTheme(workspaceId, {
        puck_data: data,
      });

      if (!response.success) {
        throw new Error(response.message || 'Failed to publish theme');
      }

      toast.success('Theme published successfully!');

    } catch (error) {
      console.error('Save failed:', error);
      toast.error('Failed to save changes');
    } finally {
      setSaving(false);
    }
  };

  // Silent auto-save function - no UI feedback, pure magic
  const silentAutoSave = useCallback(
    async (data: Data) => {
      try {
        if (!workspaceId) return; // Skip if no workspace context

        // Auto-save to workspace as draft
        await themeCustomizationService.updateWorkspaceTheme(workspaceId, {
          puck_data: data,
        });
        // No console logs, no notifications - completely silent
      } catch (error) {
        // Silently fail - user never knows about network issues
        // Template will be saved on next successful change or manual save
      }
    },
    [workspaceId]
  );

  const handleChange = useCallback((data: Data) => {
    lastDataRef.current = data;

    // Clear any existing timeout
    if (autoSaveTimeoutRef.current) {
      clearTimeout(autoSaveTimeoutRef.current);
    }

    // Silent auto-save after 2 seconds of inactivity
    autoSaveTimeoutRef.current = setTimeout(() => {
      silentAutoSave(data);
    }, 2000);
  }, [silentAutoSave]);

  // Cleanup timeouts on unmount
  useEffect(() => {
    return () => {
      if (autoSaveTimeoutRef.current) {
        clearTimeout(autoSaveTimeoutRef.current);
      }
    };
  }, []);

  // Loading state - check both theme and workspace loading
  if (isLoading || isLoadingWorkspace) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Loading Editor</h3>
          <p className="text-gray-500">
            {isLoadingWorkspace ? 'Loading workspace theme...' : 'Preparing your template editor...'}
          </p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="h-screen flex items-center justify-center bg-red-50">
        <div className="text-center max-w-md">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="h-8 w-8 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Editor Error</h3>
          <p className="text-red-600 text-sm mb-6">{error}</p>
          <button
            onClick={() => window.history.back()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  // No workspace context - redirect to theme selection
  if (!isLoading && !isLoadingWorkspace && !workspaceId) {
    return (
      <div className="h-screen flex items-center justify-center bg-yellow-50">
        <div className="text-center max-w-md">
          <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="h-8 w-8 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 15.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Workspace Selected</h3>
          <p className="text-gray-600 text-sm mb-6">Please select a workspace to edit this theme.</p>
          <button
            onClick={() => router.push('/showcase')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Browse Themes
          </button>
        </div>
      </div>
    );
  }

  return (
    <>
      {/* Only show manual save feedback - auto-save is completely invisible */}
      {saving && (
        <div className="fixed top-4 right-4 z-50 bg-green-600 text-white px-4 py-2 rounded-lg shadow-lg flex items-center gap-2">
          <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          Saving...
        </div>
      )}
      
      <Editor
        workspaceId={workspaceId || undefined}
        templateData={workspaceTheme?.customization?.puckData}
        onPublish={handlePublish}
        onChange={handleChange}
      />
    </>
  );
}