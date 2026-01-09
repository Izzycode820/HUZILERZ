'use client';

import { Button } from '@/components/shadcn-ui/button';
import { Image, X } from 'lucide-react';
import { useMediaLibrary } from '../MediaLibraryProvider';

interface ImagePickerProps {
  value: string;
  onChange: (value: string) => void;
  onOpenPicker?: () => void;
  name: string;
}

export function ImagePicker({ value, onChange, onOpenPicker }: ImagePickerProps) {
  const { open } = useMediaLibrary();

  const handleRemove = () => {
    onChange('');
  };

  const handleOpenPicker = () => {
    // If a custom onOpenPicker prop is passed, use it (backward compatibility)
    if (onOpenPicker) {
      onOpenPicker();
      return;
    }

    // Otherwise use the Media Library context
    open((url: string) => {
      onChange(url);
    }, { allowedTypes: ['image'] });
  };

  return (
    <div className="space-y-2">
      {value ? (
        <div className="relative group">
          <div className="border rounded-lg overflow-hidden bg-muted/30">
            <img
              src={value}
              alt="Selected"
              className="w-full h-40 object-cover"
            />
          </div>
          <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <Button
              type="button"
              variant="destructive"
              size="icon"
              className="h-7 w-7"
              onClick={handleRemove}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>
      ) : (
        <Button
          type="button"
          variant="outline"
          className="w-full h-32 flex flex-col gap-2"
          onClick={handleOpenPicker}
        >
          <Image className="h-8 w-8 text-muted-foreground" />
          <span className="text-sm">Select Image</span>
        </Button>
      )}
    </div>
  );
}
