/**
 * OptionsForm Component
 * Manages all product options and triggers variant generation
 */

import { useCallback } from 'react';
import { Button } from '@/components/shadcn-ui/button';
import { Plus } from 'lucide-react';
import type { ProductOption } from './types';
import { OptionCard } from './OptionCard';

interface OptionsFormProps {
  options: ProductOption[];
  setOptions: (options: ProductOption[]) => void;
  maxOptions?: number;
}

export function OptionsForm({
  options,
  setOptions,
  maxOptions = 3
}: OptionsFormProps) {
  const handleAddOption = () => {
    if (options.length < maxOptions) {
      setOptions([
        ...options,
        {
          optionName: "",
          optionValues: [""]
        }
      ]);
    }
  };

  const handleUpdateOption = useCallback((index: number, option: ProductOption) => {
    const updated = [...options];
    updated[index] = option;
    setOptions(updated);
  }, [options, setOptions]);

  const handleDeleteOption = (index: number) => {
    const filtered = options.filter((_, i) => i !== index);
    setOptions(filtered);
  };

  return (
    <div className="space-y-4">
      {options.map((option, index) => (
        <OptionCard
          key={`option-${index}`}
          option={option}
          index={index}
          onUpdate={handleUpdateOption}
          onDelete={handleDeleteOption}
        />
      ))}

      {options.length < maxOptions && (
        <Button
          variant="outline"
          onClick={handleAddOption}
          className="w-full"
        >
          <Plus className="mr-2 h-4 w-4" />
          Add another option {options.length > 0 && `(${maxOptions - options.length} remaining)`}
        </Button>
      )}
    </div>
  );
}
