/**
 * VariantsTable Component
 * Displays hierarchical nested variants with simplified UI
 */

import { useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/shadcn-ui/table';
import { Input } from '@/components/shadcn-ui/input';
import { Checkbox } from '@/components/shadcn-ui/checkbox';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/shadcn-ui/select';
import { Button } from '@/components/shadcn-ui/button';
import { Image as ImageIcon, Search, Filter, ChevronDown, ChevronRight, X } from 'lucide-react';
import type { ProductOption, VariantFormState } from './types';
import { VariantEditModal } from './VariantEditModal';
import { isLeafVariant, getVariantLevelValue } from './utils';
import { FilesAndMediaModal } from '@/components/workspace/store/shared/files-and-media';
import type { MediaSelection } from '@/components/workspace/store/shared/files-and-media';

interface VariantsTableProps {
  options: ProductOption[];
  variants: VariantFormState[];
  setVariants: (variants: VariantFormState[]) => void;
}

export function VariantsTable({
  options,
  variants,
  setVariants
}: VariantsTableProps) {
  const [groupBy, setGroupBy] = useState<string>("none");
  const [selectedVariants, setSelectedVariants] = useState<Set<string>>(new Set());
  const [editingVariant, setEditingVariant] = useState<VariantFormState | null>(null);
  const [showMediaModal, setShowMediaModal] = useState(false);
  const [editingImageForVariant, setEditingImageForVariant] = useState<string | null>(null);

  // Toggle variant expansion
  const toggleExpand = (variantId: string) => {
    const updateExpanded = (vars: VariantFormState[]): VariantFormState[] => {
      return vars.map(v => {
        if (v.id === variantId) {
          return { ...v, isExpanded: !v.isExpanded };
        }
        if (v.children && v.children.length > 0) {
          return { ...v, children: updateExpanded(v.children) };
        }
        return v;
      });
    };
    setVariants(updateExpanded(variants));
  };

  // Update variant (deep update through hierarchy)
  const handleVariantUpdate = (updatedVariant: VariantFormState) => {
    const updateVariant = (vars: VariantFormState[]): VariantFormState[] => {
      return vars.map(v => {
        if (v.id === updatedVariant.id) {
          return { ...v, ...updatedVariant, children: v.children };
        }
        if (v.children && v.children.length > 0) {
          return { ...v, children: updateVariant(v.children) };
        }
        return v;
      });
    };
    setVariants(updateVariant(variants));
  };

  // Open media modal for variant
  const handleOpenMediaModal = (variantId: string) => {
    setEditingImageForVariant(variantId);
    setShowMediaModal(true);
  };

  // Handle media selection from modal
  const handleMediaSelect = (selection: MediaSelection) => {
    if (!editingImageForVariant) return;

    // Get first selected item
    const selectedItem = selection.newUploads[0] || selection.existingUploads[0];

    if (selectedItem) {
      const updateVariantImage = (vars: VariantFormState[]): VariantFormState[] => {
        return vars.map(v => {
          if (v.id === editingImageForVariant) {
            return {
              ...v,
              mediaItem: selectedItem,
              featuredMediaId: selectedItem.uploadId
            };
          }
          if (v.children && v.children.length > 0) {
            return { ...v, children: updateVariantImage(v.children) };
          }
          return v;
        });
      };
      setVariants(updateVariantImage(variants));
    }

    setShowMediaModal(false);
    setEditingImageForVariant(null);
  };

  // Handle image removal for variant
  const handleImageRemove = (variantId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const updateVariantImage = (vars: VariantFormState[]): VariantFormState[] => {
      return vars.map(v => {
        if (v.id === variantId) {
          return { ...v, mediaItem: undefined, featuredMediaId: undefined };
        }
        if (v.children && v.children.length > 0) {
          return { ...v, children: updateVariantImage(v.children) };
        }
        return v;
      });
    };
    setVariants(updateVariantImage(variants));
  };

  // Flatten variants for rendering
  const flattenVariants = (vars: VariantFormState[], level = 0): Array<VariantFormState & { renderLevel: number }> => {
    const result: Array<VariantFormState & { renderLevel: number }> = [];

    vars.forEach(v => {
      result.push({ ...v, renderLevel: level });
      if (v.isExpanded && v.children && v.children.length > 0) {
        result.push(...flattenVariants(v.children, level + 1));
      }
    });

    return result;
  };

  const flatVariants = flattenVariants(variants);

  return (
    <>
      <div className="space-y-4">
        {/* Controls */}
        {options.length > 1 && (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-muted-foreground">Group by</span>
              <Select value={groupBy} onValueChange={setGroupBy}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="None" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">None</SelectItem>
                  {options.map((opt, idx) => (
                    <SelectItem key={idx} value={`option${idx + 1}`}>
                      {opt.optionName}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center gap-2">
              <Button variant="outline" size="icon">
                <Search className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="icon">
                <Filter className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}

        {/* Variants Table */}
        <div className="border rounded-lg overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/50">
                <TableHead className="w-12">
                  <Checkbox />
                </TableHead>
                <TableHead className="w-[80px]">Image</TableHead>
                <TableHead>Variant</TableHead>
                <TableHead className="w-[150px]">Price (FCFA)</TableHead>
                <TableHead className="w-[120px]">Available</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {flatVariants.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                    No variants yet. Add option values above to create variants.
                  </TableCell>
                </TableRow>
              ) : (
                flatVariants.map((variant) => {
                  const hasChildren = variant.children && variant.children.length > 0;
                  const isLeaf = isLeafVariant(variant);
                  const variantValue = getVariantLevelValue(variant);
                  const indentPx = variant.renderLevel * 40; // Indentation for all elements

                  return (
                    <TableRow key={variant.id} className={hasChildren ? 'bg-muted/30' : ''}>
                      {/* Checkbox - Indented */}
                      <TableCell>
                        <div style={{ paddingLeft: `${indentPx}px` }}>
                          <Checkbox />
                        </div>
                      </TableCell>

                      {/* Image Upload - ALL rows have image */}
                      <TableCell>
                        <div style={{ paddingLeft: `${indentPx}px` }}>
                          {variant.mediaItem ? (
                            <div className="relative group h-12 w-12">
                              <img
                                src={variant.mediaItem.thumbnailUrl || variant.mediaItem.url}
                                alt={variantValue}
                                className="h-12 w-12 object-cover rounded border"
                              />
                              <button
                                type="button"
                                onClick={(e) => handleImageRemove(variant.id!, e)}
                                className="absolute -top-1 -right-1 bg-destructive text-destructive-foreground rounded-full p-0.5 opacity-0 group-hover:opacity-100 transition-opacity"
                              >
                                <X className="h-3 w-3" />
                              </button>
                            </div>
                          ) : (
                            <Button
                              type="button"
                              variant="outline"
                              size="icon"
                              className="h-12 w-12 hover:bg-accent"
                              onClick={() => handleOpenMediaModal(variant.id!)}
                            >
                              <ImageIcon className="h-4 w-4 text-muted-foreground" />
                            </Button>
                          )}
                        </div>
                      </TableCell>

                      {/* Variant Value (Clickable for leaf, expandable for parents) */}
                      <TableCell>
                        <div
                          className="flex items-center gap-2"
                          style={{ paddingLeft: `${indentPx}px` }}
                        >
                          {hasChildren && (
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-5 w-5 p-0 flex-shrink-0"
                              onClick={() => toggleExpand(variant.id!)}
                            >
                              {variant.isExpanded ? (
                                <ChevronDown className="h-4 w-4" />
                              ) : (
                                <ChevronRight className="h-4 w-4" />
                              )}
                            </Button>
                          )}

                          {isLeaf ? (
                            <button
                              onClick={() => setEditingVariant(variant)}
                              className="text-left hover:underline font-medium"
                            >
                              {variantValue}
                            </button>
                          ) : (
                            <span className="font-medium">{variantValue}</span>
                          )}

                          {hasChildren && (
                            <span className="text-sm text-muted-foreground ml-1">
                              {variant.children!.length} variant{variant.children!.length > 1 ? 's' : ''}
                            </span>
                          )}
                        </div>
                      </TableCell>

                      {/* Price (Editable ONLY for leaf nodes) */}
                      <TableCell>
                        {isLeaf ? (
                          <Input
                            type="number"
                            placeholder="0"
                            value={variant.price || ""}
                            onChange={(e) =>
                              handleVariantUpdate({
                                ...variant,
                                price: parseFloat(e.target.value) || undefined
                              })
                            }
                            className="w-full"
                          />
                        ) : (
                          <span className="text-muted-foreground text-sm">-</span>
                        )}
                      </TableCell>

                      {/* Available (Editable for leaf) */}
                      <TableCell>
                        {isLeaf ? (
                          <Input
                            type="number"
                            placeholder="0"
                            value={variant.inventoryQuantity || ""}
                            onChange={(e) =>
                              handleVariantUpdate({
                                ...variant,
                                inventoryQuantity: parseInt(e.target.value) || 0
                              })
                            }
                            className="w-full"
                          />
                        ) : (
                          <span className="text-muted-foreground text-sm">-</span>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </div>

        {/* Summary */}
        {flatVariants.length > 0 && (
          <div className="text-sm text-muted-foreground">
            Inventory is not tracked at Shop location
          </div>
        )}
      </div>

      {/* Edit Modal */}
      {editingVariant && (
        <VariantEditModal
          open={!!editingVariant}
          onOpenChange={(open) => !open && setEditingVariant(null)}
          variant={editingVariant}
          onSave={handleVariantUpdate}
        />
      )}

      {/* Media Modal for Variant Images */}
      <FilesAndMediaModal
        open={showMediaModal}
        onClose={() => {
          setShowMediaModal(false);
          setEditingImageForVariant(null);
        }}
        onSelect={handleMediaSelect}
        allowedTypes={['image']}
        maxSelection={1}
      />
    </>
  );
}
