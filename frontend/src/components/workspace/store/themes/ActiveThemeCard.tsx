'use client';

import React from 'react';
import Image from 'next/image';
import { Card, CardContent } from '@/components/shadcn-ui/card';
import { Badge } from '@/components/shadcn-ui/badge';
import { Button } from '@/components/shadcn-ui/button';
import { Calendar, Package } from 'lucide-react';

interface ActiveThemeCardProps {
  id: string;
  themeName: string;
  previewImage: string;
  version: string;
  createdAt: string;
  onEditTheme: () => void;
}

export function ActiveThemeCard({
  id,
  themeName,
  previewImage,
  version,
  createdAt,
  onEditTheme,
}: ActiveThemeCardProps) {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <Card className="overflow-hidden">
      <CardContent className="p-6">
        <div className="flex gap-6">
          {/* Preview Image */}
          <div className="flex-shrink-0">
            <div className="relative w-64 h-40 rounded-lg overflow-hidden border border-gray-200">
              {previewImage ? (
                <Image
                  src={previewImage}
                  alt={themeName}
                  fill
                  className="object-cover"
                />
              ) : (
                <div className="w-full h-full bg-gray-100 flex items-center justify-center">
                  <Package className="w-12 h-12 text-gray-300" />
                </div>
              )}
            </div>
          </div>

          {/* Theme Info */}
          <div className="flex-1 flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <h3 className="text-lg font-semibold text-gray-900">{themeName}</h3>
                <Badge variant="default" className="bg-green-100 text-green-800 hover:bg-green-100">
                  Current theme
                </Badge>
              </div>
              <div className="flex items-center gap-4 text-sm text-gray-600">
                <div className="flex items-center gap-1">
                  <Calendar className="w-4 h-4" />
                  <span>Added: {formatDate(createdAt)}</span>
                </div>
                <div className="flex items-center gap-1">
                  <Package className="w-4 h-4" />
                  <span>Version {version}</span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3 mt-4">
              <Button onClick={onEditTheme} size="default">
                Edit theme
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
