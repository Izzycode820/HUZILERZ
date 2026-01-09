'use client';

import { Input } from '@/components/shadcn-ui/input';
import { Slider as ShadcnSlider } from '@/components/shadcn-ui/slider';

interface SliderProps {
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
  unit?: string;
  name: string;
}

export function Slider({
  value,
  onChange,
  min = 0,
  max = 100,
  step = 1,
  unit = '',
}: SliderProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <ShadcnSlider
          value={[value]}
          onValueChange={([val]) => onChange(val)}
          min={min}
          max={max}
          step={step}
          className="flex-1"
        />
        <Input
          type="number"
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          min={min}
          max={max}
          step={step}
          className="w-20 h-9 text-sm"
        />
        {unit && <span className="text-sm text-muted-foreground w-6">{unit}</span>}
      </div>
    </div>
  );
}
