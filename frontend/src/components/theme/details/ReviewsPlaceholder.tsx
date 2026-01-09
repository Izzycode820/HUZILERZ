'use client';

import React from 'react';
import { Card, CardContent } from '@/components/shadcn-ui/card';
import { Star } from 'lucide-react';

export function ReviewsPlaceholder() {
  return (
    <section id="reviews" className="bg-white">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-gray-900 mb-8">Reviews & Ratings</h2>

          <Card>
            <CardContent className="p-12 text-center">
              <div className="flex justify-center mb-4">
                <div className="flex gap-1">
                  {[...Array(5)].map((_, i) => (
                    <Star key={i} className="w-8 h-8 text-gray-300 fill-gray-300" />
                  ))}
                </div>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Coming Soon</h3>
              <p className="text-gray-600 max-w-md mx-auto">
                We're working on adding a review system for themes. Stay tuned for user ratings and feedback!
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
}
