'use client';

import { Switch } from '@/components/shadcn-ui/switch';
import { Label } from '@/components/shadcn-ui/label';

interface ToggleProps {
  value: boolean;
  onChange: (value: boolean) => void;
  label?: string;
  description?: string;
  name: string;
}

export function Toggle({ value, onChange, label, description }: ToggleProps) {
  return (
    <div className="flex items-center justify-between gap-4 py-1">
      <div className="flex-1 space-y-0.5">
        {label && (
          <Label className="text-sm font-medium cursor-pointer">
            {label}
          </Label>
        )}
        {description && (
          <p className="text-xs text-muted-foreground">{description}</p>
        )}
      </div>
      <Switch
        checked={value}
        onCheckedChange={onChange}
      />
    </div>
  );
}
