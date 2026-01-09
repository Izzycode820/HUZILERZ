'use client';

import { useState } from 'react';
import { Input } from '@/components/shadcn-ui/input';
import { Button } from '@/components/shadcn-ui/button';
import { Link2, Link2Off } from 'lucide-react';

interface SpacingValue {
  top: number;
  right: number;
  bottom: number;
  left: number;
}

interface SpacingProps {
  value: SpacingValue;
  onChange: (value: SpacingValue) => void;
  unit?: string;
  name: string;
}

export function Spacing({ value, onChange, unit = 'px' }: SpacingProps) {
  const [isLinked, setIsLinked] = useState(
    value.top === value.right && value.right === value.bottom && value.bottom === value.left
  );

  const handleChange = (side: keyof SpacingValue, newValue: number) => {
    if (isLinked) {
      onChange({
        top: newValue,
        right: newValue,
        bottom: newValue,
        left: newValue,
      });
    } else {
      onChange({
        ...value,
        [side]: newValue,
      });
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted-foreground">
          {isLinked ? 'All sides linked' : 'Individual sides'}
        </span>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="h-6 w-6 p-0"
          onClick={() => setIsLinked(!isLinked)}
        >
          {isLinked ? (
            <Link2 className="h-3.5 w-3.5" />
          ) : (
            <Link2Off className="h-3.5 w-3.5" />
          )}
        </Button>
      </div>

      <div className="border rounded-lg p-4 bg-muted/30">
        <div className="grid grid-cols-3 gap-2">
          <div />
          <div className="flex flex-col items-center gap-1">
            <span className="text-xs text-muted-foreground">Top</span>
            <Input
              type="number"
              value={value.top}
              onChange={(e) => handleChange('top', parseFloat(e.target.value) || 0)}
              className="h-8 text-center text-sm w-16"
            />
          </div>
          <div />

          <div className="flex items-center gap-1">
            <span className="text-xs text-muted-foreground">Left</span>
            <Input
              type="number"
              value={value.left}
              onChange={(e) => handleChange('left', parseFloat(e.target.value) || 0)}
              className="h-8 text-center text-sm w-16"
            />
          </div>
          <div className="flex items-center justify-center">
            <div className="h-12 w-12 border-2 border-dashed rounded flex items-center justify-center">
              <span className="text-xs text-muted-foreground">{unit}</span>
            </div>
          </div>
          <div className="flex items-center justify-end gap-1">
            <Input
              type="number"
              value={value.right}
              onChange={(e) => handleChange('right', parseFloat(e.target.value) || 0)}
              className="h-8 text-center text-sm w-16"
            />
            <span className="text-xs text-muted-foreground">Right</span>
          </div>

          <div />
          <div className="flex flex-col items-center gap-1">
            <Input
              type="number"
              value={value.bottom}
              onChange={(e) => handleChange('bottom', parseFloat(e.target.value) || 0)}
              className="h-8 text-center text-sm w-16"
            />
            <span className="text-xs text-muted-foreground">Bottom</span>
          </div>
          <div />
        </div>
      </div>
    </div>
  );
}
