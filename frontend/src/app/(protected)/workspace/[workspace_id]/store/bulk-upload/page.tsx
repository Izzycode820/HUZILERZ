'use client';

import React, { useState, useRef } from 'react';
import { useSearchParams, useParams } from 'next/navigation';
import DashboardSidebar from '@/components/workspace/store/dashboard/DashboardSidebar';
import WorkspaceHeader from '@/components/workspace/shared/header/WorkspaceHeader';
import BulkOperations from '@/components/workspace/store/products/BulkOperations';
import RecentOperations from '@/components/workspace/store/products/RecentOperations';
import { useNotifications } from '@/hooks/shared/notifications/useNotifications';
import { useWorkspace } from '@/contexts/WorkspaceContext';

export default function BulkUploadPage() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { unreadCount } = useNotifications();
  const { currentWorkspace } = useWorkspace();
  const searchParams = useSearchParams();
  const params = useParams();
  const workspaceId = params.workspace_id as string;
  const bulkOperationsRef = useRef<{ restoreFromData: (products: any[], filename: string) => void }>(null);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-stone-900 flex">
      {/* Sidebar */}
      <DashboardSidebar 
        collapsed={!sidebarOpen}
        currentPage="bulk-upload"
        workspaceId={workspaceId || currentWorkspace?.id || ""}
        workspaceType="store"
        userTier="boss"
        className={`${
          sidebarOpen 
            ? 'translate-x-0' 
            : '-translate-x-full'
        } lg:translate-x-0 fixed lg:relative z-30 lg:z-0 transition-transform duration-300 ease-in-out`}
      />

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-20 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Workspace Header */}
      <WorkspaceHeader
        workspaceName={currentWorkspace?.name || "My Store"}
        workspaceType={currentWorkspace?.type || "store"}
        onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
        notificationCount={unreadCount}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-h-screen pt-16">
        <div className="p-4 sm:p-6 lg:p-8">
          
          <div className="space-y-6">
            {/* Main Bulk Operations - Full width */}
            <div>
              <BulkOperations 
                ref={bulkOperationsRef}
              />
            </div>
            
            {/* Recent Operations - Below bulk operations, left-aligned and compact */}
            <div className="max-w-2xl">
              <RecentOperations 
                onRestoreOperation={(products, filename) => {
                  // Call the restore method on BulkOperations component
                  bulkOperationsRef.current?.restoreFromData(products, filename);
                }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}