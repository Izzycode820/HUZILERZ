/**
 * CreateCategoryModal Component
 * Placeholder for category creation
 * Full implementation coming soon
 */

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/shadcn-ui/dialog';

interface CreateCategoryModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CreateCategoryModal({
  open,
  onOpenChange,
}: CreateCategoryModalProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Add collection</DialogTitle>
        </DialogHeader>

        <div className="flex items-center justify-center py-12">
          <div className="text-center space-y-3">
            <p className="text-lg font-medium text-muted-foreground">
              Create Category Coming Soon
            </p>
            <p className="text-sm text-muted-foreground">
              This feature will allow you to create new collections/categories directly from the product form.
            </p>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
