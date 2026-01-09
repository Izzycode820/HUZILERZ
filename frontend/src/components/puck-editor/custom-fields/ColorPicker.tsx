'use client';

import { useState } from 'react';
import { Input } from '@/components/shadcn-ui/input';
import { Button } from '@/components/shadcn-ui/button';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/shadcn-ui/popover';
import { Check } from 'lucide-react';

interface ColorPickerProps {
  value: string;
  onChange: (value: string) => void;
  name: string;
}

const PRESET_COLORS = [
  '#000000', '#FFFFFF', '#EF4444', '#F97316', '#F59E0B', '#EAB308',
  '#84CC16', '#22C55E', '#10B981', '#14B8A6', '#06B6D4', '#0EA5E9',
  '#3B82F6', '#6366F1', '#8B5CF6', '#A855F7', '#D946EF', '#EC4899',
  '#F43F5E', '#64748B', '#6B7280', '#71717A', '#78716C', '#57534E',
];

export function ColorPicker({ value, onChange }: ColorPickerProps) {
  const [customColor, setCustomColor] = useState(value || '#000000');

  const handlePresetSelect = (color: string) => {
    onChange(color);
    setCustomColor(color);
  };

  const handleCustomChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newColor = e.target.value;
    setCustomColor(newColor);
    onChange(newColor);
  };

  return (
    <div className="space-y-2">
      <Popover>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            className="w-full justify-start gap-2 h-9"
          >
            <div
              className="h-5 w-5 rounded border border-border"
              style={{ backgroundColor: value || '#000000' }}
            />
            <span className="flex-1 text-left text-sm">{value || 'Select color'}</span>
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-64 p-3" align="start">
          <div className="space-y-3">
            <div className="flex gap-2">
              <Input
                type="text"
                value={customColor}
                onChange={(e) => setCustomColor(e.target.value)}
                onBlur={() => onChange(customColor)}
                placeholder="#000000"
                className="h-8 text-sm font-mono"
              />
              <input
                type="color"
                value={customColor}
                onChange={handleCustomChange}
                className="h-8 w-12 rounded border cursor-pointer"
              />
            </div>

            <div>
              <p className="text-xs font-medium text-muted-foreground mb-2">Presets</p>
              <div className="grid grid-cols-8 gap-1.5">
                {PRESET_COLORS.map((color) => (
                  <button
                    key={color}
                    type="button"
                    className="h-7 w-7 rounded border border-border hover:scale-110 transition-transform relative"
                    style={{ backgroundColor: color }}
                    onClick={() => handlePresetSelect(color)}
                  >
                    {value === color && (
                      <Check className="h-3 w-3 absolute inset-0 m-auto text-white drop-shadow" />
                    )}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </PopoverContent>
      </Popover>
    </div>
  );
}
