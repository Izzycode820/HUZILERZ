import { usePuck } from '@measured/puck';
import { FieldRenderer } from './FieldRenderer';

export function FieldsPanel() {
  const puck = usePuck();
  const selectedItem = puck.selectedItem;

  if (!selectedItem) {
    return (
      <div className="p-4 text-muted-foreground">
        Select a section or block to edit.
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4">
      <FieldRenderer node={selectedItem} puck={puck} />
    </div>
  );
}