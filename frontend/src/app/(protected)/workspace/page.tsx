import WorkspaceDashboard from '@/components/workspace/management/WorkspaceDashboard';
import { ManagementLayoutClient } from '@/components/workspace/management/config/management-layout-client';

export default function WorkspacePage() {
  return (
    <ManagementLayoutClient>
      <WorkspaceDashboard />
    </ManagementLayoutClient>
  );
}