/**
 * ProductOrganizationSection Component
 *
 * Features:
 * - Product type selection
 * - Vendor input
 * - Category/Collection dropdown with search
 * - Add new category option
 * - Tags input (combobox style)
 */

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/shadcn-ui/card';
import { Input } from '@/components/shadcn-ui/input';
import { Label } from '@/components/shadcn-ui/label';
import { Button } from '@/components/shadcn-ui/button';
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
import { Badge } from '@/components/shadcn-ui/badge';
import { Check, ChevronDown, Plus, X, Search } from 'lucide-react';
import { cn } from '@/lib/utils';
import { CreateCategoryModal } from './CreateCategoryModal';
import type { CategoryOption } from './types';

interface ProductOrganizationSectionProps {
  productType: string;
  vendor: string;
  categoryId: string;
  tags: string[];
  categories: CategoryOption[]; // Passed from parent (fetched via query)
  onProductTypeChange: (value: string) => void;
  onVendorChange: (value: string) => void;
  onCategoryIdChange: (value: string) => void;
  onTagsChange: (tags: string[]) => void;
}

export function ProductOrganizationSection({
  productType,
  vendor,
  categoryId,
  tags,
  categories,
  onProductTypeChange,
  onVendorChange,
  onCategoryIdChange,
  onTagsChange,
}: ProductOrganizationSectionProps) {
  const [categoryOpen, setCategoryOpen] = useState(false);
  const [tagsOpen, setTagsOpen] = useState(false);
  const [tagInput, setTagInput] = useState('');
  const [createModalOpen, setCreateModalOpen] = useState(false);

  // Find selected category name
  const selectedCategory = categories.find(cat => cat.id === categoryId);

  const handleAddTag = (tag: string) => {
    const trimmed = tag.trim();
    if (trimmed && !tags.includes(trimmed)) {
      onTagsChange([...tags, trimmed]);
      setTagInput('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    onTagsChange(tags.filter(tag => tag !== tagToRemove));
  };

  const handleAddNewCategory = () => {
    setCategoryOpen(false);
    setCreateModalOpen(true);
  };

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle>Product organization</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Product Type - Dropdown with 3 options */}
          <div className="space-y-2">
            <Label htmlFor="product-type">Product Type</Label>
            <select
              id="product-type"
              value={productType}
              onChange={(e) => onProductTypeChange(e.target.value)}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            >
              <option value="physical">Physical Product</option>
              <option value="digital">Digital Product</option>
              <option value="service">Service</option>
            </select>
            <p className="text-xs text-muted-foreground">
              {productType === 'digital' && 'Downloadable files, licenses, etc.'}
              {productType === 'service' && 'Appointments, consultations, subscriptions, etc.'}
              {productType === 'physical' && 'Tangible goods that require shipping.'}
            </p>
          </div>


          {/* Vendor */}
          <div className="space-y-2">
            <Label htmlFor="vendor">Vendor</Label>
            <Input
              id="vendor"
              placeholder="e.g., Samsung, Apple"
              value={vendor}
              onChange={(e) => onVendorChange(e.target.value)}
            />
          </div>

          {/* Collections (Categories) */}
          <div className="space-y-2">
            <Label>Collections</Label>
            <Popover open={categoryOpen} onOpenChange={setCategoryOpen}>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  role="combobox"
                  aria-expanded={categoryOpen}
                  className="w-full justify-between"
                >
                  <div className="flex items-center gap-2">
                    <Search className="h-4 w-4 text-muted-foreground" />
                    <span className={cn(!selectedCategory && "text-muted-foreground")}>
                      {selectedCategory ? selectedCategory.name : "Search collections"}
                    </span>
                  </div>
                  <ChevronDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-full p-0" align="start">
                <Command>
                  <CommandInput placeholder="Search collections..." />
                  <CommandList>
                    <CommandEmpty>No collection found.</CommandEmpty>
                    <CommandGroup>
                      {/* Add new collection option */}
                      <CommandItem
                        onSelect={handleAddNewCategory}
                        className="text-primary"
                      >
                        <Plus className="mr-2 h-4 w-4" />
                        Add new collection
                      </CommandItem>

                      {/* Category list */}
                      {categories.map((category) => (
                        <CommandItem
                          key={category.id}
                          value={category.name}
                          onSelect={() => {
                            onCategoryIdChange(category.id);
                            setCategoryOpen(false);
                          }}
                        >
                          <Check
                            className={cn(
                              "mr-2 h-4 w-4",
                              categoryId === category.id ? "opacity-100" : "opacity-0"
                            )}
                          />
                          {category.name}
                        </CommandItem>
                      ))}
                    </CommandGroup>
                  </CommandList>
                </Command>
              </PopoverContent>
            </Popover>

            {/* Selected category badge */}
            {selectedCategory && (
              <div className="flex items-center gap-2 pt-2">
                <Badge variant="secondary" className="flex items-center gap-1">
                  {selectedCategory.name}
                  <button
                    onClick={() => onCategoryIdChange('')}
                    className="ml-1 hover:bg-muted rounded-full p-0.5"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              </div>
            )}
          </div>

          {/* Tags */}
          <div className="space-y-2">
            <Label>Tags</Label>
            <Popover open={tagsOpen} onOpenChange={setTagsOpen}>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  role="combobox"
                  className="w-full justify-start"
                >
                  <Search className="mr-2 h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">Search or create tags</span>
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-full p-0" align="start">
                <Command>
                  <CommandInput
                    placeholder="Type to add tag..."
                    value={tagInput}
                    onValueChange={setTagInput}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && tagInput) {
                        e.preventDefault();
                        handleAddTag(tagInput);
                      }
                    }}
                  />
                  <CommandList>
                    <CommandEmpty>
                      <Button
                        variant="ghost"
                        className="w-full justify-start"
                        onClick={() => {
                          handleAddTag(tagInput);
                          setTagsOpen(false);
                        }}
                      >
                        <Plus className="mr-2 h-4 w-4" />
                        Add "{tagInput}"
                      </Button>
                    </CommandEmpty>
                  </CommandList>
                </Command>
              </PopoverContent>
            </Popover>

            {/* Tags display */}
            {tags.length > 0 && (
              <div className="flex flex-wrap gap-2 pt-2">
                {tags.map((tag) => (
                  <Badge key={tag} variant="secondary" className="flex items-center gap-1">
                    {tag}
                    <button
                      onClick={() => handleRemoveTag(tag)}
                      className="ml-1 hover:bg-muted rounded-full p-0.5"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Create Category Modal */}
      <CreateCategoryModal
        open={createModalOpen}
        onOpenChange={setCreateModalOpen}
      />
    </>
  );
}
