'use client';

import React from 'react';
import Image from 'next/image';

interface ThemeHeroSectionProps {
  previewImage: string | null;
  themeName: string;
}

export function ThemeHeroSection({ previewImage, themeName }: ThemeHeroSectionProps) {
  return (
    <section id="overview" className="w-full bg-gray-50">
      <div className="container mx-auto px-4 py-12">
        <div className="relative w-full aspect-video rounded-lg overflow-hidden shadow-lg">
          {previewImage ? (
            <Image
              src={previewImage}
              alt={`${themeName} preview`}
              fill
              className="object-cover"
              priority
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-gray-200">
              <span className="text-gray-400 text-lg">No preview available</span>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
