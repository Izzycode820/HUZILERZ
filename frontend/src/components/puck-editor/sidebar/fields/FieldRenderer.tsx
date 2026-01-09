import { Input } from '@/components/shadcn-ui/input';
import { Label } from '@/components/shadcn-ui/label';
import { Textarea } from '@/components/shadcn-ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/shadcn-ui/select';

export function FieldRenderer({ node, puck }: { node: any; puck: any }) {
  // Get component config from puck.config
  const componentType = node.type;
  const componentConfig = puck.config.components[componentType];

  if (!componentConfig) {
    return <div className="text-sm text-muted-foreground">Component type "{componentType}" not found in config.</div>;
  }

  const fields = componentConfig.fields || {};

  // Convert fields object to array
  const fieldEntries = Object.entries(fields);

  if (fieldEntries.length === 0) {
    return <div className="text-sm text-muted-foreground">No fields defined for this component.</div>;
  }

  // Update handler - dispatches changes to Puck
  const handleFieldChange = (fieldName: string, value: any) => {
    // Find the item in puck.appState.data.content
    const contentIndex = puck.appState.data.content.findIndex(
      (item: any) => item.props.id === node.props.id
    );

    if (contentIndex === -1) {
      console.error('Could not find item in content array');
      return;
    }

    // Dispatch the update action
    puck.dispatch({
      type: 'replace',
      destinationIndex: contentIndex,
      data: {
        ...node,
        props: {
          ...node.props,
          [fieldName]: value,
        },
      },
    });
  };

  // Render field based on type
  const renderField = (fieldName: string, fieldConfig: any) => {
    const currentValue = node.props[fieldName];

    switch (fieldConfig.type) {
      case 'text':
        return (
          <Input
            value={currentValue || ''}
            onChange={(e) => handleFieldChange(fieldName, e.target.value)}
            placeholder={fieldConfig.placeholder || ''}
          />
        );

      case 'textarea':
        return (
          <Textarea
            value={currentValue || ''}
            onChange={(e) => handleFieldChange(fieldName, e.target.value)}
            placeholder={fieldConfig.placeholder || ''}
            rows={4}
          />
        );

      case 'number':
        return (
          <Input
            type="number"
            value={currentValue || ''}
            onChange={(e) => handleFieldChange(fieldName, parseFloat(e.target.value) || 0)}
            placeholder={fieldConfig.placeholder || ''}
            min={fieldConfig.min}
            max={fieldConfig.max}
          />
        );

      case 'select':
        return (
          <Select
            value={currentValue || ''}
            onValueChange={(value) => handleFieldChange(fieldName, value)}
          >
            <SelectTrigger>
              <SelectValue placeholder={fieldConfig.placeholder || 'Select...'} />
            </SelectTrigger>
            <SelectContent>
              {fieldConfig.options?.map((option: any) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        );

      case 'array':
        // For arrays, show a simple list for now
        // TODO: Implement full array editor with add/remove/reorder
        return (
          <div className="text-sm text-muted-foreground">
            Array editing (coming soon)
          </div>
        );

      default:
        return (
          <Input
            value={currentValue || ''}
            onChange={(e) => handleFieldChange(fieldName, e.target.value)}
            placeholder={fieldConfig.placeholder || ''}
          />
        );
    }
  };

  return (
    <div className="space-y-4">
      <div className="pb-2 border-b">
        <h3 className="font-semibold text-sm">{componentConfig.label || componentType}</h3>
      </div>
      {fieldEntries.map(([fieldName, fieldConfig]: [string, any]) => (
        <div key={fieldName} className="space-y-2">
          <Label className="text-sm font-medium">{fieldConfig.label || fieldName}</Label>
          {renderField(fieldName, fieldConfig)}
        </div>
      ))}
    </div>
  );
}