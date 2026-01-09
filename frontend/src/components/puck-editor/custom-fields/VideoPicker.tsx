'use client';

import { Button } from '@/components/shadcn-ui/button';
import { Video, X } from 'lucide-react';
import { useMediaLibrary } from '../MediaLibraryProvider';

interface VideoPickerProps {
    value: string;
    onChange: (value: string) => void;
    onOpenPicker?: () => void;
    name: string;
}

export function VideoPicker({ value, onChange, onOpenPicker }: VideoPickerProps) {
    const { open } = useMediaLibrary();

    const handleRemove = () => {
        onChange('');
    };

    const handleOpenPicker = () => {
        if (onOpenPicker) {
            onOpenPicker();
            return;
        }

        open((url: string) => {
            onChange(url);
        }, { allowedTypes: ['video'] });
    };

    return (
        <div className="space-y-2">
            {value ? (
                <div className="relative group">
                    <div className="border rounded-lg overflow-hidden bg-muted/30 aspect-video">
                        <video
                            src={value}
                            className="w-full h-full object-cover"
                            controls
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
                    <Video className="h-8 w-8 text-muted-foreground" />
                    <span className="text-sm">Select Video</span>
                </Button>
            )}
        </div>
    );
}
