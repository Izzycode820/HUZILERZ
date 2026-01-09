import { Button } from '@/components/shadcn-ui/button';
import { GripVertical, Trash2 } from 'lucide-react';

interface OutlineNodeProps {
  item: any;
  index: number;
  label: string;
  isSelected: boolean;
  puck: any;
}

export function OutlineNode({ item, index, label, isSelected, puck }: OutlineNodeProps) {
  const handleSelect = () => {
    // Select this item in Puck
    puck.dispatch({
      type: 'setUi',
      ui: {
        ...puck.appState.ui,
        itemSelector: {
          index,
          zone: 'default-zone',
        },
      },
    });
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();

    // Remove this item from content
    puck.dispatch({
      type: 'remove',
      index,
    });
  };

  // Get a preview of the content (first text field value)
  const getPreview = (): string | null => {
    const firstTextField = Object.entries(item.props).find(
      ([key, value]) => typeof value === 'string' && key !== 'id' && value.length > 0
    );

    if (firstTextField) {
      const [, value] = firstTextField;
      return typeof value === 'string' && value.length > 30
        ? `${value.substring(0, 30)}...`
        : value as string;
    }
    return null;
  };

  const preview = getPreview();

  return (
    <div
      className={`group flex items-center gap-2 px-2 py-1.5 rounded-md transition-colors cursor-pointer hover:bg-accent ${isSelected ? 'bg-accent border-l-2 border-primary' : ''
        }`}
      onClick={handleSelect}
    >
      <GripVertical className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />

      <div className="flex-1 min-w-0">
        <div className="font-medium text-sm truncate">{label}</div>
        {preview && (
          <div className="text-xs text-muted-foreground truncate">{preview}</div>
        )}
      </div>

      <Button
        variant="ghost"
        size="icon"
        className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
        onClick={handleDelete}
      >
        <Trash2 className="h-3 w-3" />
      </Button>
    </div>
  );
}