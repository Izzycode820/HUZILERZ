'use client';

import React, { createContext, useContext, useState, ReactNode, useCallback } from 'react';
import { FilesAndMediaModal, MediaSelection } from '@/components/workspace/store/shared/files-and-media';
import { ApolloProvider } from '@apollo/client/react';
import { adminStoreClient } from '@/services/graphql/clients';

// --- Types ---
interface MediaLibraryContextType {
    open: (onSelect: (url: string) => void, opts?: { allowedTypes?: ('image' | 'video' | '3d_model')[] }) => void;
    close: () => void;
}

interface OpenOptions {
    onSelect: (url: string) => void;
    allowedTypes?: ('image' | 'video' | '3d_model')[];
}

// --- Context ---
const MediaLibraryContext = createContext<MediaLibraryContextType | undefined>(undefined);

// --- Hook ---
export function useMediaLibrary() {
    const context = useContext(MediaLibraryContext);
    if (!context) {
        throw new Error('useMediaLibrary must be used within a MediaLibraryProvider');
    }
    return context;
}

// --- Provider ---
interface MediaLibraryProviderProps {
    children: ReactNode;
}

export function MediaLibraryProvider({ children }: MediaLibraryProviderProps) {
    const [isOpen, setIsOpen] = useState(false);
    const [options, setOptions] = useState<Omit<OpenOptions, 'onSelect'>>({});
    // We store the current callback for the active picker interaction
    const [onSelectCallback, setOnSelectCallback] = useState<((url: string) => void) | null>(null);

    /**
     * Opens the media library modal.
     * @param onSelect - Callback function that receives the selected media URL.
     * @param opts - Optional configuration like allowedTypes.
     */
    const open = useCallback((onSelect: (url: string) => void, opts: { allowedTypes?: ('image' | 'video' | '3d_model')[] } = {}) => {
        setOnSelectCallback(() => onSelect);
        setOptions(opts);
        setIsOpen(true);
    }, []);

    const close = useCallback(() => {
        setIsOpen(false);
        setOnSelectCallback(null);
        setOptions({});
    }, []);

    const handleMediaSelect = (selection: MediaSelection) => {
        // Determine the URL to return. 
        // Logic: Look for new uploads first, then existing ones.
        // Since this is a single picker, we generally expect one item.
        // If the user selects multiple, we'll take the first one.

        let selectedUrl = '';

        if (selection.newUploads.length > 0) {
            selectedUrl = selection.newUploads[0].url;
        } else if (selection.existingUploads.length > 0) {
            selectedUrl = selection.existingUploads[0].url;
        }

        if (selectedUrl && onSelectCallback) {
            onSelectCallback(selectedUrl);
        }

        // Auto-close after selection for a smoother experience
        close();
    };

    return (
        <MediaLibraryContext.Provider value={{ open, close }}>
            {children}

            <ApolloProvider client={adminStoreClient}>
                <FilesAndMediaModal
                    open={isOpen}
                    onClose={close}
                    onSelect={handleMediaSelect}
                    // Customize these as needed or make them dynamic via open() args if necessary in future
                    allowedTypes={options.allowedTypes || ['image', 'video']}
                    maxSelection={1}
                    selectedItems={[]} // We don't need to show pre-selected items for this simple picker yet
                />
            </ApolloProvider>
        </MediaLibraryContext.Provider>
    );
}
