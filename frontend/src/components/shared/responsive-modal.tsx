'use client'

import * as React from 'react'
import { X } from 'lucide-react'
import { useIsMobile } from '@/hooks/shadcn/use-mobile'
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogFooter,
    DialogClose,
} from '@/components/shadcn-ui/dialog'
import {
    Drawer,
    DrawerContent,
    DrawerHeader,
    DrawerTitle,
    DrawerFooter,
    DrawerClose,
} from '@/components/shadcn-ui/drawer'
import { Button } from '@/components/shadcn-ui/button'
import { cn } from '@/lib/utils'

interface ResponsiveModalProps {
    /** Whether the modal is open */
    open: boolean
    /** Callback when modal should close */
    onClose: () => void
    /** Modal title */
    title: string
    /** Modal content */
    children: React.ReactNode
    /** Optional footer content */
    footer?: React.ReactNode
    /** Optional className for dialog content (desktop) */
    dialogClassName?: string
    /** Optional className for drawer content (mobile) */
    drawerClassName?: string
    /** Whether to show close button - defaults to true */
    showCloseButton?: boolean
    /** Optional description for accessibility */
    description?: string
}

/**
 * ResponsiveModal - A modal component that adapts to screen size
 * 
 * Desktop: Renders as a centered Dialog
 * Mobile: Renders as a full-screen Drawer (Shopify pattern)
 * 
 * This prevents code bloat in individual modals while providing
 * an optimal UX for both form factors.
 */
export function ResponsiveModal({
    open,
    onClose,
    title,
    children,
    footer,
    dialogClassName,
    drawerClassName,
    showCloseButton = true,
    description,
}: ResponsiveModalProps) {
    const isMobile = useIsMobile()

    // Handle undefined state during SSR/hydration
    if (isMobile === undefined) {
        return null
    }

    // Mobile: Full-screen drawer (Shopify pattern)
    if (isMobile) {
        return (
            <Drawer open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
                <DrawerContent
                    className={cn(
                        // Full screen mobile layout
                        'h-[100dvh] max-h-[100dvh] rounded-none',
                        // Remove default drawer styling for full-screen
                        'inset-x-0 bottom-0 mt-0',
                        drawerClassName
                    )}
                >
                    {/* Mobile Header - Shopify style */}
                    <DrawerHeader className="flex flex-row items-center justify-between border-b px-4 py-3">
                        <DrawerClose asChild>
                            <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8"
                                aria-label="Close"
                            >
                                <X className="h-5 w-5" />
                            </Button>
                        </DrawerClose>
                        <DrawerTitle className="text-base font-semibold">
                            {title}
                        </DrawerTitle>
                        {/* Spacer for centering title */}
                        <div className="w-8" />
                    </DrawerHeader>

                    {/* Scrollable content area */}
                    <div className="flex-1 overflow-y-auto">
                        {children}
                    </div>

                    {/* Mobile Footer */}
                    {footer && (
                        <DrawerFooter className="border-t px-4 py-3">
                            {footer}
                        </DrawerFooter>
                    )}
                </DrawerContent>
            </Drawer>
        )
    }

    // Desktop: Centered dialog
    return (
        <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
            <DialogContent
                className={cn(
                    'max-w-lg',
                    dialogClassName
                )}
            >
                <DialogHeader>
                    <DialogTitle>{title}</DialogTitle>
                    {description && (
                        <p className="text-sm text-muted-foreground">{description}</p>
                    )}
                </DialogHeader>

                {children}

                {footer && (
                    <DialogFooter>
                        {footer}
                    </DialogFooter>
                )}
            </DialogContent>
        </Dialog>
    )
}

/**
 * ResponsiveModalContent - Content wrapper with proper padding
 */
export function ResponsiveModalContent({
    children,
    className,
}: {
    children: React.ReactNode
    className?: string
}) {
    return (
        <div className={cn('px-4 py-3 md:px-6 md:py-4', className)}>
            {children}
        </div>
    )
}

/**
 * ResponsiveModalFooter - Standardized footer with action buttons
 */
export function ResponsiveModalFooter({
    children,
    className,
}: {
    children: React.ReactNode
    className?: string
}) {
    return (
        <div className={cn('flex items-center justify-end gap-2', className)}>
            {children}
        </div>
    )
}

export { type ResponsiveModalProps }
