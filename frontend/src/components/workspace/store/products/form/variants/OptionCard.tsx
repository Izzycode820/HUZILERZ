/**
 * OptionCard Component
 * Displays and edits a single product option (e.g., Color, Size)
 * with its values (e.g., Blue, Small)
 * Supports collapsed/expanded accordion state
 */

import { useState, useEffect } from 'react';
import { Input } from '@/components/shadcn-ui/input';
import { Label } from '@/components/shadcn-ui/label';
import { Button } from '@/components/shadcn-ui/button';
import { GripVertical, X, MinusCircle } from 'lucide-react';
import { ProductOption } from './types';
import { Badge } from '@/components/shadcn-ui/badge';

interface OptionCardProps {
  option: ProductOption;
  index: number;
  onUpdate: (index: number, option: ProductOption) => void;
  onDelete: (index: number) => void;
}

export function OptionCard({
  option,
  index,
  onUpdate,
  onDelete
}: OptionCardProps) {
  const [optionName, setOptionName] = useState(option.optionName || "");
  const [optionValues, setOptionValues] = useState<string[]>(
    option.optionValues.length > 0 ? option.optionValues : [""]
  );
  const [isCollapsed, setIsCollapsed] = useState(option.isCollapsed || false);

  // Update parent when local state changes
  useEffect(() => {
    const filteredValues = optionValues.filter(v => v.trim() !== "");
    if (filteredValues.length > 0 || optionName.trim() !== "") {
      onUpdate(index, {
        optionName: optionName,
        optionValues: filteredValues,
        isCollapsed: isCollapsed
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [optionName, optionValues, index, isCollapsed]);

  const handleValueChange = (valueIndex: number, value: string) => {
    const updated = [...optionValues];
    updated[valueIndex] = value;
    setOptionValues(updated);
  };

  const handleRemoveValue = (valueIndex: number) => {
    const updated = optionValues.filter((_, i) => i !== valueIndex);
    setOptionValues(updated.length > 0 ? updated : [""]);
  };

  const handleAddValue = () => {
    setOptionValues([...optionValues, ""]);
  };

  const handleDone = () => {
    if (optionName.trim() && optionValues.some(v => v.trim())) {
      setIsCollapsed(true);
    }
  };

  const handleExpand = () => {
    setIsCollapsed(false);
  };

  // Collapsed view (minimized)
  if (isCollapsed) {
    return (
      <div
        className="border rounded-lg p-3 bg-card hover:bg-accent/50 cursor-pointer transition-colors"
        onClick={handleExpand}
      >
        <div className="flex items-center gap-2">
          <GripVertical className="h-4 w-4 text-muted-foreground flex-shrink-0" />
          <div className="flex-1">
            <div className="font-medium text-sm">{optionName}</div>
            <div className="flex flex-wrap gap-1 mt-1">
              {optionValues.filter(v => v.trim()).map((value, idx) => (
                <Badge key={idx} variant="secondary" className="text-xs">
                  {value}
                </Badge>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Expanded view (full form)
  return (
    <div className="border rounded-lg p-4 space-y-4 bg-card">
      <div className="flex items-start gap-2">
        {/* Drag Handle */}
        <GripVertical className="h-5 w-5 text-muted-foreground mt-2 cursor-move flex-shrink-0" />

        <div className="flex-1 space-y-3">
          {/* Option Name */}
          <div>
            <Label htmlFor={`option-name-${index}`} className="text-sm font-medium">
              Option name
            </Label>
            <Input
              id={`option-name-${index}`}
              placeholder="e.g., Color, Size, Material"
              value={optionName}
              onChange={(e) => setOptionName(e.target.value)}
              className="mt-1.5"
            />
          </div>

          {/* Option Values */}
          <div>
            <Label className="text-sm font-medium">Option values</Label>
            <div className="space-y-2 mt-1.5">
              {optionValues.map((value, valueIndex) => (
                <div key={valueIndex} className="flex items-center gap-2">
                  <GripVertical className="h-4 w-4 text-muted-foreground cursor-move flex-shrink-0" />
                  <Input
                    placeholder={valueIndex === 0 ? "e.g., Blue" : "e.g., Black"}
                    value={value}
                    onChange={(e) => handleValueChange(valueIndex, e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && valueIndex === optionValues.length - 1) {
                        handleAddValue();
                      }
                    }}
                    className="flex-1"
                  />
                  {optionValues.length > 1 && (
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleRemoveValue(valueIndex)}
                      className="flex-shrink-0"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              ))}

              {/* Add another value button */}
              <Button
                variant="outline"
                size="sm"
                onClick={handleAddValue}
                className="w-full text-muted-foreground"
              >
                Add another value
              </Button>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-between pt-2 border-t">
            <Button
              variant="destructive"
              size="sm"
              onClick={() => onDelete(index)}
            >
              Delete
            </Button>
            <Button
              size="sm"
              onClick={handleDone}
              disabled={!optionName.trim() || !optionValues.some(v => v.trim())}
            >
              Done
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
