'use client';

import React from 'react';
import Image from 'next/image';
import { Card, CardContent } from '@/components/shadcn-ui/card';
import { Badge } from '@/components/shadcn-ui/badge';
import { Button } from '@/components/shadcn-ui/button';

interface ShowcaseSection {
  title: string | null;
  description: string | null;
  image: string | null;
}

interface ThemeDetailsSectionProps {
  name: string;
  description: string;
  author: string;
  priceTier: string;
  priceAmount: number;
  showcaseSections: ShowcaseSection[];
  demoUrl?: string | null;
  onUseTheme: () => void;
}

export function ThemeDetailsSection({
  name,
  description,
  author,
  priceTier,
  priceAmount,
  showcaseSections,
  demoUrl,
  onUseTheme,
}: ThemeDetailsSectionProps) {
  const formatPrice = () => {
    if (priceTier === 'free') return 'Free';
    if (priceTier === 'exclusive') return 'Exclusive';
    return `$${priceAmount}`;
  };

  return (
    <section className="bg-white">
      <div className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Main Content */}
          <div className="lg:col-span-2 space-y-8">
            {/* Theme Title & Description */}
            <div>
              <h2 className="text-3xl font-bold text-gray-900 mb-3">{name}</h2>
              <p className="text-gray-600 text-lg leading-relaxed">{description}</p>
              <div className="flex items-center gap-4 mt-4">
                <span className="text-sm text-gray-500">by {author}</span>
              </div>
            </div>

            {/* Showcase Sections */}
            {showcaseSections && showcaseSections.length > 0 && (
              <div className="space-y-8">
                <h3 className="text-xl font-semibold text-gray-900">What's Included</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {showcaseSections.map((section, index) => (
                    <Card key={index} className="overflow-hidden">
                      {section.image && (
                        <div className="relative w-full aspect-video">
                          <Image
                            src={section.image}
                            alt={section.title || 'Showcase'}
                            fill
                            className="object-cover"
                          />
                        </div>
                      )}
                      <CardContent className="p-4">
                        <h4 className="font-semibold text-gray-900 mb-2">{section.title || 'Untitled'}</h4>
                        <p className="text-sm text-gray-600">{section.description || ''}</p>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right Column - Sidebar */}
          <div className="lg:col-span-1">
            <div className="sticky top-24">
              <Card>
                <CardContent className="p-6 space-y-6">
                  {/* Price */}
                  <div>
                    <div className="text-3xl font-bold text-gray-900">{formatPrice()}</div>
                    {priceTier !== 'free' && (
                      <p className="text-sm text-gray-500 mt-1">One-time payment</p>
                    )}
                  </div>

                  {/* Action Buttons */}
                  <div className="space-y-3">
                    <Button onClick={onUseTheme} className="w-full" size="lg">
                      Use Theme
                    </Button>
                    {demoUrl && (
                      <Button
                        variant="outline"
                        className="w-full"
                        size="lg"
                        onClick={() => window.open(demoUrl, '_blank')}
                      >
                        View Demo
                      </Button>
                    )}
                  </div>

                  {/* Price Tier Badge */}
                  <div className="flex items-center justify-center pt-4 border-t">
                    <Badge variant="secondary" className="text-xs">
                      {priceTier.toUpperCase()}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
