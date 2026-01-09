import { usePuck } from '@measured/puck';
import { OutlineNode } from './OutlineNode';

export function OutlineTree() {
  const puck = usePuck();

  // Get the content array from Puck data
  const content = puck.appState.data.content || [];

  // Get currently selected item
  const selectedItem = puck.selectedItem;

  if (content.length === 0) {
    return (
      <div className="p-4 text-sm text-muted-foreground text-center">
        No components yet. Add components from the Blocks tab.
      </div>
    );
  }

  return (
    <div className="p-2 space-y-1 overflow-y-auto">
      {content.map((item: any, index: number) => {
        const componentConfig = puck.config.components[item.type];
        const isSelected = selectedItem?.props.id === item.props.id;

        return (
          <OutlineNode
            key={item.props.id || index}
            item={item}
            index={index}
            label={componentConfig?.label || item.type}
            isSelected={isSelected}
            puck={puck}
          />
        );
      })}
    </div>
  );
}