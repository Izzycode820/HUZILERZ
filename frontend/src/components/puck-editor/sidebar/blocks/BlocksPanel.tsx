import { usePuck } from '@measured/puck';
import { BlockItem } from './BlockItem';

export function BlocksPanel() {
  const puck = usePuck();

  // Get all components from config
  const components = puck.config.components || {};
  const categories = puck.config.categories || {};

  // If categories are defined, organize by category
  const hasCategoriesorganized = Object.keys(categories).length > 0;

  if (Object.keys(components).length === 0) {
    return (
      <div className="p-4 text-sm text-muted-foreground text-center">
        No components available
      </div>
    );
  }

  // Render with categories
  if (hasCategoriesorganized) {
    return (
      <div className="p-2 space-y-4">
        {Object.entries(categories).map(([categoryKey, category]: [string, any]) => (
          <div key={categoryKey}>
            <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 px-2">
              {category.title || categoryKey}
            </h3>
            <div className="grid gap-2">
              {category.components?.map((componentType: string) => {
                const componentConfig = components[componentType];
                if (!componentConfig) return null;

                return (
                  <BlockItem
                    key={componentType}
                    block={{
                      type: componentType,
                      label: componentConfig.label || componentType,
                      description: (componentConfig as any).description || '',
                    }}
                    puck={puck}
                  />
                );
              })}
            </div>
          </div>
        ))}
      </div>
    );
  }

  // Render without categories (flat list)
  return (
    <div className="p-2 grid gap-2">
      {Object.entries(components).map(([componentType, componentConfig]: [string, any]) => (
        <BlockItem
          key={componentType}
          block={{
            type: componentType,
            label: componentConfig.label || componentType,
            description: (componentConfig as any).description || '',
          }}
          puck={puck}
        />
      ))}
    </div>
  );
}