'use client';

import React, { useState } from 'react';
import { useParams } from 'next/navigation';
import DashboardSidebar from '@/components/workspace/store/dashboard/DashboardSidebar';
import WorkspaceHeader from '@/components/workspace/shared/header/WorkspaceHeader';
import { Users } from 'lucide-react';
import { useNotifications } from '@/hooks/shared/notifications/useNotifications';
import { useWorkspace } from '@/contexts/WorkspaceContext';

export default function StoreUsersPage() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { unreadCount } = useNotifications();
  const { currentWorkspace } = useWorkspace();
  const params = useParams();
  const workspaceId = params.workspace_id as string;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-stone-900 flex">
      {/* Sidebar */}
      <DashboardSidebar 
        collapsed={!sidebarOpen}
        currentPage="users"
        workspaceId={workspaceId || currentWorkspace?.id || ""}
        workspaceType={currentWorkspace?.type || "store"}
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
        <div className="flex-1 p-4 sm:p-6 lg:p-8">
          {/* Placeholder Content */}
          <div className="bg-white dark:bg-stone-800 rounded-lg border border-gray-200 dark:border-gray-700 p-12 text-center">
            <div className="w-16 h-16 mx-auto mb-6 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center">
              <Users className="w-8 h-8 text-blue-600 dark:text-blue-400" />
            </div>
            
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
              Users & Team
            </h1>
            
            <p className="text-gray-600 dark:text-gray-300 mb-8 max-w-md mx-auto">
              Manage your store team members and customer accounts from your hosted websites.
            </p>

            <div className="space-y-4">
              <div className="bg-gray-50 dark:bg-stone-700 rounded-lg p-6">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Coming Soon:</h3>
                <ul className="text-sm text-gray-600 dark:text-gray-300 space-y-1">
                  <li>• Team member invitation and role management</li>
                  <li>• Staff permissions and access control</li>
                  <li>• Customer account management from hosted stores</li>
                  <li>• Purchase history and customer analytics</li>
                  <li>• User activity tracking and engagement metrics</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}