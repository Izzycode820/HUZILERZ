'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Plus, FolderPlus } from 'lucide-react';
import StaticHeader from '@/components/landing-page/StaticHeader';
import TemplateCard, { UserTemplate } from '@/components/my-templates/TemplateCard';
import FilterBar from '@/components/my-templates/FilterBar';
import EmptyState from '@/components/my-templates/EmptyState';
import { getUserTemplates, GetTemplatesResponse } from '@/components/my-templates/api';

export default function MyTemplatesPage() {
  const router = useRouter();
  const [templates, setTemplates] = useState<UserTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalCount, setTotalCount] = useState(0);
  
  // Filter states
  const [statusFilter, setStatusFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  useEffect(() => {
    loadUserTemplates();
  }, [statusFilter, searchQuery]);

  const loadUserTemplates = async () => {
    try {
      setLoading(true);
      
      const params = {
        status: statusFilter === 'all' ? undefined : statusFilter,
        search: searchQuery || undefined,
        sort_by: 'updated',
        page_size: 50,
      };

      const response: GetTemplatesResponse = await getUserTemplates(params);
      setTemplates(response.templates);
      setTotalCount(response.pagination.total_count);
    } catch (error) {
      console.error('Failed to load templates:', error);
      // Fallback to empty state on error
      setTemplates([]);
      setTotalCount(0);
    } finally {
      setLoading(false);
    }
  };

  const handleBrowseTemplates = () => {
    router.push('/showcase');
  };

  const handleCreateNew = () => {
    router.push('/showcase');
  };

  const handleTemplateClick = (template: UserTemplate) => {
    // Set context in sessionStorage for reliable detection
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('editor_context', 'my-templates');
    }
    
    // Navigate to editor with the template and source parameter
    router.push(`/showcase/editor/${template.id}?source=my-templates`);
  };

  if (loading) {
    return (
      <>
        <StaticHeader />
        <div className="min-h-screen bg-gray-50 dark:bg-stone-900 pt-16">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="animate-pulse">
              {/* Header Skeleton */}
              <div className="flex justify-between items-start mb-8">
                <div>
                  <div className="h-10 bg-gray-200 dark:bg-stone-700 rounded-lg mb-2 w-64"></div>
                  <div className="h-4 bg-gray-200 dark:bg-stone-700 rounded-lg w-96"></div>
                </div>
                <div className="h-12 bg-gray-200 dark:bg-stone-700 rounded-lg w-48"></div>
              </div>
              
              {/* Filter Bar Skeleton */}
              <div className="h-16 bg-gray-200 dark:bg-stone-700 rounded-lg mb-8"></div>
              
              {/* Templates Grid Skeleton */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {Array.from({ length: 6 }).map((_, i) => (
                  <div key={i} className="h-80 bg-gray-200 dark:bg-stone-700 rounded-xl"></div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <StaticHeader />
      <div className="min-h-screen bg-gray-50 dark:bg-stone-900 pt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Header - Wix Style */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-8">
            <div>
              <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white mb-2">
                My Templates
              </h1>
              <p className="text-gray-600 dark:text-gray-300">
                View and manage all your templates in one place.
              </p>
            </div>
            
            <div className="flex gap-3 mt-4 sm:mt-0">
              <button
                onClick={handleBrowseTemplates}
                className="px-4 py-2 border border-blue-600 text-blue-600 dark:text-blue-400 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors flex items-center gap-2"
              >
                <FolderPlus className="h-4 w-4" />
                Browse Marketplace
              </button>
              <button
                onClick={handleCreateNew}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
              >
                <Plus className="h-4 w-4" />
                Create New Template
              </button>
            </div>
          </div>

          {/* Filter Bar */}
          <div className="mb-6">
            <FilterBar
              totalCount={totalCount}
              statusFilter={statusFilter}
              searchQuery={searchQuery}
              viewMode={viewMode}
              onStatusFilterChange={setStatusFilter}
              onSearchChange={setSearchQuery}
              onViewModeChange={setViewMode}
            />
          </div>

          {/* Templates Grid */}
          {templates.length > 0 ? (
            <div className={`grid gap-6 ${
              viewMode === 'grid' 
                ? 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3' 
                : 'grid-cols-1'
            }`}>
              {templates.map((template) => (
                <TemplateCard
                  key={template.id}
                  template={template}
                  onClick={() => handleTemplateClick(template)}
                />
              ))}
            </div>
          ) : (
            <EmptyState 
              onBrowseTemplates={handleBrowseTemplates} 
              statusFilter={statusFilter}
            />
          )}
        </div>
      </div>
    </>
  );
}