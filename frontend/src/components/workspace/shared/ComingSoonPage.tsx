'use client';

import React from 'react';
import { Clock, ArrowRight, Star } from 'lucide-react';

interface ComingSoonPageProps {
  title: string;
  description?: string;
  expectedDate?: string;
  features?: string[];
  workspaceType: 'store' | 'blog' | 'services';
}

export default function ComingSoonPage({
  title,
  description = "This feature is currently under development and will be available soon.",
  expectedDate = "Coming Soon",
  features = [],
  workspaceType
}: ComingSoonPageProps) {
  const getWorkspaceColor = () => {
    switch (workspaceType) {
      case 'store':
        return 'blue';
      case 'blog':
        return 'purple';
      case 'services':
        return 'green';
      default:
        return 'blue';
    }
  };

  const colorClasses = {
    blue: 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 border-blue-200 dark:border-blue-800',
    purple: 'bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 border-purple-200 dark:border-purple-800',
    green: 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 border-green-200 dark:border-green-800'
  };

  const color = getWorkspaceColor();

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-stone-900 flex items-center justify-center p-4">
      <div className="max-w-2xl mx-auto text-center">
        {/* Icon */}
        <div className={`w-20 h-20 mx-auto mb-8 rounded-full flex items-center justify-center ${colorClasses[color]}`}>
          <Clock className="w-10 h-10" />
        </div>

        {/* Title */}
        <h1 className="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white mb-4">
          {title}
        </h1>

        {/* Description */}
        <p className="text-lg text-gray-600 dark:text-gray-300 mb-8 max-w-lg mx-auto leading-relaxed">
          {description}
        </p>

        {/* Expected Date */}
        <div className={`inline-flex items-center px-4 py-2 rounded-full border ${colorClasses[color]} mb-8`}>
          <Star className="w-4 h-4 mr-2" />
          <span className="text-sm font-medium">{expectedDate}</span>
        </div>

        {/* Features Preview */}
        {features.length > 0 && (
          <div className="bg-white dark:bg-stone-800 rounded-lg border border-gray-200 dark:border-stone-700 p-6 mb-8">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              What to expect:
            </h3>
            <div className="space-y-3">
              {features.map((feature, index) => (
                <div key={index} className="flex items-center text-left">
                  <ArrowRight className="w-4 h-4 text-gray-400 mr-3 flex-shrink-0" />
                  <span className="text-gray-600 dark:text-gray-300">{feature}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Back Button */}
        <button
          onClick={() => window.history.back()}
          className={`px-6 py-3 rounded-lg font-medium transition-colors bg-${color}-600 hover:bg-${color}-700 dark:bg-${color}-500 dark:hover:bg-${color}-600 text-white`}
        >
          Back to Dashboard
        </button>
      </div>
    </div>
  );
}