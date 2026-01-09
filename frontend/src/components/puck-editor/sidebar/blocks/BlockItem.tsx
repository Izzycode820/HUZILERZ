import { Card } from '@/components/shadcn-ui/card';
import { Plus } from 'lucide-react';

interface BlockItemProps {
  block: {
    type: string;
    label: string;
    description?: string;
  };
  puck: any;
}

export function BlockItem({ block, puck }: BlockItemProps) {
  const handleAddBlock = () => {
    // Get the component config to use default props
    const componentConfig = puck.config.components[block.type];
    const defaultProps = componentConfig?.defaultProps || {};

    // Generate a unique ID for the new component
    const id = `${block.type}-${Date.now()}`;

    // Add the block to the end of the content array
    puck.dispatch({
      type: 'insert',
      componentType: block.type,
      destinationIndex: puck.appState.data.content.length,
      destinationZone: 'default-zone',
      id,
    });
  };

  return (
    <Card
      className="group relative p-3 cursor-pointer hover:bg-accent hover:border-primary transition-all"
      onClick={handleAddBlock}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="font-medium text-sm truncate">{block.label}</div>
          {block.description && (
            <div className="text-xs text-muted-foreground line-clamp-2 mt-1">
              {block.description}
            </div>
          )}
        </div>
        <Plus className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
      </div>
    </Card>
  );
}