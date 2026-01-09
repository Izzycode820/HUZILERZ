'use client';

import React from 'react';
import { Card, CardContent } from '@/components/shadcn-ui/card';

interface FeatureCategory {
  category: string | null;
  items: (string | null)[] | null;
}

interface ThemeFeaturesSectionProps {
  features: FeatureCategory[];
}

export function ThemeFeaturesSection({ features }: ThemeFeaturesSectionProps) {
  if (!features || features.length === 0) {
    return null;
  }

  return (
    <section id="features" className="bg-gray-50">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-gray-900 mb-12">Features</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((featureCategory, categoryIndex) => (
              <div key={categoryIndex} className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-900">
                  {featureCategory.category || 'Features'}
                </h3>
                <ul className="space-y-3">
                  {(featureCategory.items || [])
                    .filter((item): item is string => item !== null)
                    .map((item, itemIndex) => (
                      <li key={itemIndex} className="text-sm text-gray-600">
                        {item}
                      </li>
                    ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
