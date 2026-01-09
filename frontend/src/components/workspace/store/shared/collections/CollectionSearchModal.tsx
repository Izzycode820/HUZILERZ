import { useState, useMemo, useEffect } from 'react';
import { Search, Check } from 'lucide-react';
import { ResponsiveModal } from '@/components/shared/responsive-modal';
import { Input } from '@/components/shadcn-ui/input';
import { Button } from '@/components/shadcn-ui/button';
import { Checkbox } from '@/components/shadcn-ui/checkbox';
import { useQuery } from '@apollo/client/react';
import { useIsMobile } from '@/hooks/shadcn/use-mobile';
import { CategoriesDocument } from '@/services/graphql/admin-store/queries/categories/__generated__/categories.generated';
import type { CollectionSearchModalProps } from './types';

export function CollectionSearchModal(props: CollectionSearchModalProps) {
    const {
        open,
        onOpenChange,
        selectedCollectionIds,
        onAddCollections,
    } = props;

    const isMobile = useIsMobile();
    const [searchTerm, setSearchTerm] = useState('');
    const [localSelectedIds, setLocalSelectedIds] = useState<string[]>(selectedCollectionIds);

    useEffect(() => {
        if (open) {
            setLocalSelectedIds(selectedCollectionIds);
        }
    }, [open, selectedCollectionIds]);

    const { data, loading } = useQuery(CategoriesDocument, {
        variables: {
            search: searchTerm,
            first: 50,
        },
        skip: !open,
    });

    const collections = useMemo(() => {
        return (
            data?.categories?.edges
                ?.map(edge => edge?.node)
                .filter((node): node is NonNullable<typeof node> => node != null) || []
        );
    }, [data]);

    const handleToggleCollection = (collectionId: string) => {
        setLocalSelectedIds(prev =>
            prev.includes(collectionId)
                ? prev.filter(id => id !== collectionId)
                : [...prev, collectionId]
        );
    };

    const handleAdd = () => {
        const newlySelectedIds = localSelectedIds.filter(id => !selectedCollectionIds.includes(id));
        const newlySelectedCollections = collections.filter(c => newlySelectedIds.includes(c.id));
        const finalSelectedCollections = collections.filter(c => localSelectedIds.includes(c.id));
        onAddCollections(finalSelectedCollections);

        onOpenChange(false);
        setSearchTerm('');
    };

    // Footer content
    const footerContent = (
        <div className="flex w-full items-center justify-between">
            <p className="text-sm text-muted-foreground">
                {localSelectedIds.length} collection{localSelectedIds.length !== 1 ? 's' : ''} selected
            </p>
            <div className="flex gap-2">
                <Button variant="outline" onClick={() => onOpenChange(false)}>
                    Cancel
                </Button>
                <Button
                    onClick={handleAdd}
                    disabled={localSelectedIds.length === 0}
                >
                    Add {localSelectedIds.length > 0 ? localSelectedIds.length : ''} collection{localSelectedIds.length !== 1 ? 's' : ''}
                </Button>
            </div>
        </div>
    );

    return (
        <ResponsiveModal
            open={open}
            onClose={() => onOpenChange(false)}
            title="Select collections"
            dialogClassName="max-w-4xl max-h-[80vh] flex flex-col"
            footer={footerContent}
        >
            <div className="flex flex-col gap-4 px-4 md:px-6 py-4 flex-1 min-h-0">
                {/* Search Input */}
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                        placeholder="Search collections..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="pl-9"
                        autoFocus={!isMobile}
                    />
                </div>

                {/* Collections List */}
                <div className="flex-1 overflow-auto border rounded-md">
                    {isMobile ? (
                        // Mobile: Card-based list
                        <div className="divide-y">
                            {loading ? (
                                <div className="text-center p-8 text-muted-foreground">
                                    Loading collections...
                                </div>
                            ) : collections.length === 0 ? (
                                <div className="text-center p-8 text-muted-foreground">
                                    No collections found
                                </div>
                            ) : (
                                collections.map((collection) => {
                                    const isSelected = localSelectedIds.includes(collection.id);
                                    return (
                                        <div
                                            key={collection.id}
                                            className="flex items-center gap-3 p-3 hover:bg-muted/30"
                                            onClick={() => handleToggleCollection(collection.id)}
                                        >
                                            <Checkbox
                                                checked={isSelected}
                                                onCheckedChange={() => handleToggleCollection(collection.id)}
                                            />
                                            <div className="flex-shrink-0 w-12 h-12 bg-muted rounded overflow-hidden">
                                                {collection.featuredMedia?.thumbnailUrl ? (
                                                    <img
                                                        src={collection.featuredMedia.thumbnailUrl}
                                                        alt={collection.name}
                                                        className="w-full h-full object-cover"
                                                    />
                                                ) : (
                                                    <div className="w-full h-full" />
                                                )}
                                            </div>
                                            <span className="font-medium text-sm flex-1 truncate">{collection.name}</span>
                                            {isSelected && (
                                                <Check className="h-4 w-4 text-primary shrink-0" />
                                            )}
                                        </div>
                                    );
                                })
                            )}
                        </div>
                    ) : (
                        // Desktop: Table layout
                        <table className="w-full">
                            <thead className="bg-muted/50 sticky top-0">
                                <tr className="border-b">
                                    <th className="w-12 p-3"></th>
                                    <th className="text-left p-3 text-sm font-medium">Collection</th>
                                    <th className="w-24 text-right p-3 text-sm font-medium">Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {loading ? (
                                    <tr>
                                        <td colSpan={3} className="text-center p-8 text-muted-foreground">
                                            Loading collections...
                                        </td>
                                    </tr>
                                ) : collections.length === 0 ? (
                                    <tr>
                                        <td colSpan={3} className="text-center p-8 text-muted-foreground">
                                            No collections found
                                        </td>
                                    </tr>
                                ) : (
                                    collections.map((collection) => {
                                        const isSelected = localSelectedIds.includes(collection.id);
                                        return (
                                            <tr key={collection.id} className="border-b hover:bg-muted/30">
                                                <td className="p-3">
                                                    <Checkbox
                                                        checked={isSelected}
                                                        onCheckedChange={() => handleToggleCollection(collection.id)}
                                                    />
                                                </td>
                                                <td className="p-3">
                                                    <div className="flex items-center gap-3">
                                                        <div className="flex-shrink-0 w-10 h-10 bg-muted rounded overflow-hidden">
                                                            {collection.featuredMedia?.thumbnailUrl ? (
                                                                <img
                                                                    src={collection.featuredMedia.thumbnailUrl}
                                                                    alt={collection.name}
                                                                    className="w-full h-full object-cover"
                                                                />
                                                            ) : (
                                                                <div className="w-full h-full" />
                                                            )}
                                                        </div>
                                                        <span className="font-medium text-sm">{collection.name}</span>
                                                    </div>
                                                </td>
                                                <td className="p-3 text-right">
                                                    {isSelected && (
                                                        <span className="inline-flex items-center text-xs text-muted-foreground">
                                                            <Check className="h-3 w-3 mr-1" />
                                                            Added
                                                        </span>
                                                    )}
                                                </td>
                                            </tr>
                                        );
                                    })
                                )}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>
        </ResponsiveModal>
    );
}

