'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/shadcn-ui/card';
import Link from 'next/link';
import { useWorkspaceStore, workspaceSelectors } from '@/stores/authentication/workspaceStore';

type LockedSectionProps = {
    title: string;
    requiredPlan: string;
    height?: string;
};

export function LockedSection({ title, requiredPlan, height = 'h-64' }: LockedSectionProps) {
    const currentWorkspace = useWorkspaceStore(workspaceSelectors.currentWorkspace);

    return (
        <Card className="relative overflow-hidden">
            <CardHeader>
                <CardTitle>{title}</CardTitle>
            </CardHeader>
            <CardContent className={`${height} relative`}>
                {/* Blurred background */}
                <div className="absolute inset-0 backdrop-blur-sm bg-background/50" />

                {/* Centered text */}
                <div className="absolute inset-0 flex items-center justify-center">
                    <Link
                        href={`/workspace/${currentWorkspace?.id}/store/settings/plan`}
                        className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                    >
                        Data not available for {currentWorkspace?.subscription?.tier || 'current'} plan
                    </Link>
                </div>
            </CardContent>
        </Card>
    );
}
