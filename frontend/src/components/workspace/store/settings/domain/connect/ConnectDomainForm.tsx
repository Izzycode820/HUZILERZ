'use client';

import React, { useState } from 'react';
import { useMutation } from '@apollo/client/react';
import { useRouter, useParams } from 'next/navigation';
import { ConnectCustomDomainDocument } from '@/services/graphql/domains/mutations/custom-domains/__generated__/connectCustomDomain.generated';
import { useIsMobile } from '@/hooks/shadcn/use-mobile';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/shadcn-ui/dialog';
import { Button } from '@/components/shadcn-ui/button';
import { Input } from '@/components/shadcn-ui/input';
import { Label } from '@/components/shadcn-ui/label';
import { X } from 'lucide-react';
import { toast } from 'sonner';

interface ConnectDomainFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ConnectDomainForm({ open, onOpenChange }: ConnectDomainFormProps) {
  const router = useRouter();
  const params = useParams();
  const workspaceId = params.workspace_id as string;
  const [domain, setDomain] = useState('');
  const isMobile = useIsMobile();

  const [connectDomain, { loading }] = useMutation(ConnectCustomDomainDocument);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!domain) {
      toast.error('Please enter a domain');
      return;
    }

    try {
      const { data } = await connectDomain({
        variables: {
          workspaceId,
          domain: domain.toLowerCase().trim(),
        },
      });

      if (data?.connectCustomDomain?.success && data.connectCustomDomain.domain) {
        toast.success('Domain connected successfully');
        router.push(
          `/workspace/${workspaceId}/store/settings/domains/verification/${data.connectCustomDomain.domain.id}`
        );
      } else {
        toast.error(data?.connectCustomDomain?.error || 'Failed to connect domain');
      }
    } catch (err: any) {
      toast.error(err.message || 'Failed to connect domain');
      console.error('Connect domain error:', err);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <DialogTitle className="text-xl font-semibold">Connect existing domain</DialogTitle>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => onOpenChange(false)}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6 pt-4">
          <div className="space-y-2">
            <Label htmlFor="domain" className="text-sm font-medium">Domain</Label>
            <Input
              id="domain"
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              placeholder="steve.com"
              className="h-10"
              autoFocus={!isMobile}
            />
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={loading}
              className="px-4"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={!domain || loading}
              className="px-6 bg-black hover:bg-black/90 text-white"
            >
              {loading ? 'Connecting...' : 'Next'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
