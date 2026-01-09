'use client';

import React from 'react';
import { Card, CardContent } from '@/components/shadcn-ui/card';
import { Grid3x3 } from 'lucide-react';

export function RelatedThemesPlaceholder() {
  return (
    <section className="bg-gray-50">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-gray-900 mb-8">Related Themes</h2>

          <Card>
            <CardContent className="p-12 text-center">
              <div className="flex justify-center mb-4">
                <Grid3x3 className="w-16 h-16 text-gray-300" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Coming Soon</h3>
              <p className="text-gray-600 max-w-md mx-auto">
                We'll soon show themes similar to this one based on category and features.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
}
