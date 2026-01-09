'use client';

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import {
    IconArchive,
    IconTrash,
    IconDotsVertical,
    IconCopy,
} from '@tabler/icons-react';
import { FolderPlus, FolderMinus, Check, ChevronsUpDown } from 'lucide-react';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/shadcn-ui/dropdown-menu';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/shadcn-ui/dialog';
import {
    Command,
    CommandEmpty,
    CommandGroup,
    CommandInput,
    CommandItem,
    CommandList,
} from '@/components/shadcn-ui/command';
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from '@/components/shadcn-ui/popover';
import { Button } from '@/components/shadcn-ui/button';
import { useMutation, useQuery } from '@apollo/client/react';
import { AddProductsToCategoryDocument } from '@/services/graphql/admin-store/mutations/categories/__generated__/addProductsToCategory.generated';
import { RemoveProductsFromCategoryDocument } from '@/services/graphql/admin-store/mutations/categories/__generated__/removeProductsFromCategory.generated';
import { CategoriesDocument } from '@/services/graphql/admin-store/queries/categories/__generated__/categories.generated';
import { toast } from 'sonner';

interface MobileProductsActionBarProps {
    selectedCount: number;
    selectedProductIds?: string[];
    onCancel: () => void;
    onArchive: () => void;
    onDelete: () => void;
    onDuplicate?: () => void;
    onExport?: () => void;
    onCategoryUpdate?: () => void;
}

export function MobileProductsActionBar({
    selectedCount,
    selectedProductIds = [],
    onCancel,
    onArchive,
    onDelete,
    onDuplicate,
    onExport,
    onCategoryUpdate,
}: MobileProductsActionBarProps) {
    const [showAddCategoryDialog, setShowAddCategoryDialog] = useState(false);
    const [showRemoveCategoryDialog, setShowRemoveCategoryDialog] = useState(false);
    const [selectedCategory, setSelectedCategory] = useState<string>('');

    // GraphQL mutations
    const [addProductsToCategory] = useMutation(AddProductsToCategoryDocument);
    const [removeProductsFromCategory] = useMutation(RemoveProductsFromCategoryDocument);

    // Fetch categories
    const { data: categoriesData } = useQuery(CategoriesDocument, {
        variables: { first: 100, isVisible: true }
    });

    const categories = categoriesData?.categories?.edges?.map(edge => edge?.node).filter(Boolean) || [];

    const handleBulkAddToCategory = () => {
        setShowAddCategoryDialog(true);
    };

    const handleBulkRemoveFromCategory = () => {
        setShowRemoveCategoryDialog(true);
    };

    const confirmBulkAddToCategory = async () => {
        if (!selectedCategory) {
            toast.error('Please select a category');
            return;
        }

        if (selectedProductIds.length === 0) {
            toast.error('No products selected');
            return;
        }

        try {
            const { data } = await addProductsToCategory({
                variables: {
                    categoryId: selectedCategory,
                    productIds: selectedProductIds
                }
            });

            if (data?.addProductsToCategory?.success) {
                toast.success(`${selectedProductIds.length} products added to category`);
                setShowAddCategoryDialog(false);
                setSelectedCategory('');
                onCategoryUpdate?.();
            } else {
                toast.error(data?.addProductsToCategory?.error || 'Failed to add products to category');
            }
        } catch (err: any) {
            toast.error(err.message || 'Failed to add products to category');
            console.error('Bulk add to category error:', err);
        }
    };

    const confirmBulkRemoveFromCategory = async () => {
        if (!selectedCategory) {
            toast.error('Please select a category');
            return;
        }

        if (selectedProductIds.length === 0) {
            toast.error('No products selected');
            return;
        }

        try {
            const { data } = await removeProductsFromCategory({
                variables: {
                    categoryId: selectedCategory,
                    productIds: selectedProductIds
                }
            });

            if (data?.removeProductsFromCategory?.success) {
                toast.success(`${selectedProductIds.length} products removed from category`);
                setShowRemoveCategoryDialog(false);
                setSelectedCategory('');
                onCategoryUpdate?.();
            } else {
                toast.error(data?.removeProductsFromCategory?.error || 'Failed to remove products from category');
            }
        } catch (err: any) {
            toast.error(err.message || 'Failed to remove products from category');
            console.error('Bulk remove from category error:', err);
        }
    };
    if (selectedCount === 0) return null;

    return (
        <div className="fixed bottom-20 left-0 right-0 z-40 flex justify-center px-4 md:hidden pointer-events-none">
            <div className="flex items-center gap-2 bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 rounded-full px-4 py-3 shadow-2xl pointer-events-auto">
                {/* Close / Cancel Selection */}
                <button
                    onClick={onCancel}
                    className="p-2 rounded-full hover:bg-white/10 dark:hover:bg-zinc-900/10 transition-colors"
                    aria-label="Cancel selection"
                >
                    <span className="text-lg">✕</span>
                </button>

                {/* Selected Count */}
                <span className="text-sm font-medium px-2 min-w-[60px] text-center">
                    {selectedCount} selected
                </span>

                {/* Divider */}
                <div className="h-6 w-px bg-white/20 dark:bg-zinc-900/20" />

                {/* Primary Actions */}
                <button
                    onClick={onArchive}
                    className="p-2 rounded-full hover:bg-white/10 dark:hover:bg-zinc-900/10 transition-colors"
                    aria-label="Archive"
                    title="Archive"
                >
                    <IconArchive className="w-5 h-5" />
                </button>

                <button
                    onClick={onDelete}
                    className="p-2 rounded-full hover:bg-white/10 dark:hover:bg-zinc-900/10 transition-colors text-red-400"
                    aria-label="Delete"
                    title="Delete"
                >
                    <IconTrash className="w-5 h-5" />
                </button>

                {/* Overflow Menu */}
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <button
                            className="p-2 rounded-full hover:bg-white/10 dark:hover:bg-zinc-900/10 transition-colors"
                            aria-label="More actions"
                        >
                            <IconDotsVertical className="w-5 h-5" />
                        </button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent
                        align="end"
                        side="top"
                        className="w-48 mb-2"
                    >
                        {onDuplicate && (
                            <DropdownMenuItem onClick={onDuplicate}>
                                <IconCopy className="mr-2 h-4 w-4" />
                                Duplicate
                            </DropdownMenuItem>
                        )}
                        {onExport && (
                            <DropdownMenuItem onClick={onExport}>
                                Export Selected
                            </DropdownMenuItem>
                        )}
                        <DropdownMenuSeparator />
                        <DropdownMenuItem onClick={handleBulkAddToCategory}>
                            <FolderPlus className="mr-2 h-4 w-4" />
                            Add to category
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={handleBulkRemoveFromCategory}>
                            <FolderMinus className="mr-2 h-4 w-4" />
                            Remove from category
                        </DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenu>
            </div>

            {/* Bulk Add to Category Dialog */}
            <Dialog open={showAddCategoryDialog} onOpenChange={setShowAddCategoryDialog}>
                <DialogContent className="mx-4">
                    <DialogHeader>
                        <DialogTitle>Add to Category</DialogTitle>
                        <DialogDescription>
                            Select a category to add {selectedProductIds.length} selected products to.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4">
                        <Popover>
                            <PopoverTrigger asChild>
                                <Button
                                    variant="outline"
                                    role="combobox"
                                    className="w-full justify-between"
                                >
                                    {selectedCategory
                                        ? categories.find((category) => category?.id === selectedCategory)?.name
                                        : "Select category..."}
                                    <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                                </Button>
                            </PopoverTrigger>
                            <PopoverContent className="w-full p-0">
                                <Command>
                                    <CommandInput placeholder="Search categories..." />
                                    <CommandList>
                                        <CommandEmpty>No category found.</CommandEmpty>
                                        <CommandGroup>
                                            {categories.map((category) => (
                                                <CommandItem
                                                    key={category?.id}
                                                    value={category?.id || ''}
                                                    onSelect={() => setSelectedCategory(category?.id || '')}
                                                >
                                                    <Check
                                                        className={cn(
                                                            "mr-2 h-4 w-4",
                                                            selectedCategory === category?.id ? "opacity-100" : "opacity-0"
                                                        )}
                                                    />
                                                    {category?.name}
                                                </CommandItem>
                                            ))}
                                        </CommandGroup>
                                    </CommandList>
                                </Command>
                            </PopoverContent>
                        </Popover>
                    </div>
                    <DialogFooter>
                        <Button
                            variant="outline"
                            onClick={() => setShowAddCategoryDialog(false)}
                        >
                            Cancel
                        </Button>
                        <Button onClick={confirmBulkAddToCategory}>
                            Add to Category
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Bulk Remove from Category Dialog */}
            <Dialog open={showRemoveCategoryDialog} onOpenChange={setShowRemoveCategoryDialog}>
                <DialogContent className="mx-4">
                    <DialogHeader>
                        <DialogTitle>Remove from Category</DialogTitle>
                        <DialogDescription>
                            Select a category to remove {selectedProductIds.length} selected products from.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4">
                        <Popover>
                            <PopoverTrigger asChild>
                                <Button
                                    variant="outline"
                                    role="combobox"
                                    className="w-full justify-between"
                                >
                                    {selectedCategory
                                        ? categories.find((category) => category?.id === selectedCategory)?.name
                                        : "Select category..."}
                                    <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                                </Button>
                            </PopoverTrigger>
                            <PopoverContent className="w-full p-0">
                                <Command>
                                    <CommandInput placeholder="Search categories..." />
                                    <CommandList>
                                        <CommandEmpty>No category found.</CommandEmpty>
                                        <CommandGroup>
                                            {categories.map((category) => (
                                                <CommandItem
                                                    key={category?.id}
                                                    value={category?.id || ''}
                                                    onSelect={() => setSelectedCategory(category?.id || '')}
                                                >
                                                    <Check
                                                        className={cn(
                                                            "mr-2 h-4 w-4",
                                                            selectedCategory === category?.id ? "opacity-100" : "opacity-0"
                                                        )}
                                                    />
                                                    {category?.name}
                                                </CommandItem>
                                            ))}
                                        </CommandGroup>
                                    </CommandList>
                                </Command>
                            </PopoverContent>
                        </Popover>
                    </div>
                    <DialogFooter>
                        <Button
                            variant="outline"
                            onClick={() => setShowRemoveCategoryDialog(false)}
                        >
                            Cancel
                        </Button>
                        <Button onClick={confirmBulkRemoveFromCategory}>
                            Remove from Category
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
