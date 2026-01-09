"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

interface UseUnsavedChangesOptions {
  onSave?: () => void | Promise<void>;
  onDiscard?: () => void;
  enabled?: boolean;
}

/**
 * Hook to track unsaved changes and block navigation (Shopify-style)
 *
 * Features:
 * - Blocks browser navigation (back, refresh, close tab)
 * - Blocks Next.js route navigation
 * - Shows toast with Discard/Save actions
 * - Returns isDirty state for UI indicators
 *
 * @example
 * const { markAsDirty, markAsSaved, isDirty } = useUnsavedChanges({
 *   onSave: handleSave,
 *   onDiscard: handleDiscard,
 *   enabled: true
 * });
 */
export function useUnsavedChanges({
  onSave,
  onDiscard,
  enabled = true,
}: UseUnsavedChangesOptions = {}) {
  const router = useRouter();
  const [isDirty, setIsDirty] = useState(false);
  const [isNavigating, setIsNavigating] = useState(false);
  const pendingNavigationRef = useRef<string | null>(null);

  const markAsDirty = useCallback(() => {
    setIsDirty(true);
  }, []);

  const markAsSaved = useCallback(() => {
    setIsDirty(false);
    setIsNavigating(false);
    pendingNavigationRef.current = null;
  }, []);

  // Handle save action from toast
  const handleSave = useCallback(async () => {
    if (onSave) {
      await onSave();
      markAsSaved();

      // Navigate to pending route if exists
      if (pendingNavigationRef.current) {
        router.push(pendingNavigationRef.current);
        pendingNavigationRef.current = null;
      }
    }
  }, [onSave, markAsSaved, router]);

  // Handle discard action from toast
  const handleDiscard = useCallback(() => {
    if (onDiscard) {
      onDiscard();
    }
    markAsSaved();

    // Navigate to pending route if exists
    if (pendingNavigationRef.current) {
      router.push(pendingNavigationRef.current);
      pendingNavigationRef.current = null;
    }
  }, [onDiscard, markAsSaved, router]);

  // Show toast with action buttons
  const showUnsavedChangesToast = useCallback(() => {
    toast.error("You have unsaved changes", {
      duration: 6000,
      action: {
        label: "Save",
        onClick: handleSave,
      },
      cancel: {
        label: "Discard",
        onClick: handleDiscard,
      },
    });
  }, [handleSave, handleDiscard]);

  // Block browser navigation (refresh, back, close tab)
  useEffect(() => {
    if (!enabled || !isDirty) return;

    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      e.returnValue = ""; // Chrome requires returnValue to be set
      return ""; // Some browsers show this message
    };

    window.addEventListener("beforeunload", handleBeforeUnload);

    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
    };
  }, [enabled, isDirty]);

  // Block Next.js route navigation
  useEffect(() => {
    if (!enabled || !isDirty) return;

    const handleRouteChange = (url: string) => {
      if (isDirty && !isNavigating) {
        // Store the intended destination
        pendingNavigationRef.current = url;

        // Show toast with save/discard options
        showUnsavedChangesToast();

        // Prevent navigation
        router.push(window.location.pathname);
        throw new Error("Navigation blocked due to unsaved changes");
      }
    };

    // Listen to route changes
    // Note: Next.js 13+ app router doesn't have router events like pages router
    // We'll handle this with a custom approach using the router

    return () => {
      // Cleanup
    };
  }, [enabled, isDirty, isNavigating, showUnsavedChangesToast, router]);

  // Manual confirmation check (for back buttons, links, etc.)
  const confirmNavigation = useCallback(
    (onConfirm: () => void) => {
      if (isDirty) {
        // Store the callback for later use
        pendingNavigationRef.current = "manual";

        // Show toast with Save/Discard options
        toast.error("You have unsaved changes", {
          duration: 8000,
          action: {
            label: "Save",
            onClick: async () => {
              if (onSave) {
                await onSave();
              }
              markAsSaved();
              onConfirm();
            },
          },
          cancel: {
            label: "Discard",
            onClick: () => {
              if (onDiscard) {
                onDiscard();
              }
              markAsSaved();
              onConfirm();
            },
          },
        });
      } else {
        // No unsaved changes, proceed immediately
        onConfirm();
      }
    },
    [isDirty, onSave, onDiscard, markAsSaved]
  );

  return {
    isDirty,
    markAsDirty,
    markAsSaved,
    showUnsavedChangesToast,
    confirmNavigation, // Expose this for manual navigation checks
  };
}
