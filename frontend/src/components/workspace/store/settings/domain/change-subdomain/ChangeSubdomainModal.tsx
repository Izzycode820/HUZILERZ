'use client';

import React, { useState, useEffect } from 'react';
import { useMutation, useLazyQuery } from '@apollo/client/react';
import { ChangeSubdomainDocument } from '@/services/graphql/domains/mutations/subdomains/__generated__/changeSubdomain.generated';
import { ValidateSubdomainDocument } from '@/services/graphql/domains/queries/subdomains/__generated__/validateSubdomain.generated';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/shadcn-ui/dialog';
import { Button } from '@/components/shadcn-ui/button';
import { Input } from '@/components/shadcn-ui/input';
import { Alert, AlertDescription } from '@/components/shadcn-ui/alert';
import { Info, X } from 'lucide-react';
import { toast } from 'sonner';

interface ChangeSubdomainModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  workspaceId: string;
  currentSubdomain?: string;
  changesRemaining: number;
  changesLimit: number;
  onSuccess: () => void;
}

export function ChangeSubdomainModal({
  open,
  onOpenChange,
  workspaceId,
  currentSubdomain,
  changesRemaining,
  changesLimit,
  onSuccess,
}: ChangeSubdomainModalProps) {
  const [subdomain, setSubdomain] = useState('');
  const [validationError, setValidationError] = useState<string | null>(null);

  const [validateSubdomain, { data: validationData, loading: validating }] = useLazyQuery(
    ValidateSubdomainDocument
  );

  const [changeSubdomain, { loading: changing }] = useMutation(ChangeSubdomainDocument);

  useEffect(() => {
    if (subdomain && subdomain.length > 0) {
      const timer = setTimeout(() => {
        validateSubdomain({
          variables: { subdomain },
        });
      }, 500);

      return () => clearTimeout(timer);
    } else {
      setValidationError(null);
    }
  }, [subdomain, validateSubdomain]);

  useEffect(() => {
    if (validationData?.validateSubdomain) {
      const validation = validationData.validateSubdomain;
      if (!validation.available && validation.errors && validation.errors.length > 0) {
        setValidationError(validation.errors[0]);
      } else {
        setValidationError(null);
      }
    }
  }, [validationData]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!subdomain || validationError) {
      return;
    }

    try {
      const { data } = await changeSubdomain({
        variables: {
          workspaceId,
          subdomain,
        },
      });

      if (data?.changeSubdomain?.success) {
        toast.success(data.changeSubdomain.message || 'Subdomain changed successfully');
        onSuccess();
      } else {
        toast.error(data?.changeSubdomain?.error || 'Failed to change subdomain');
      }
    } catch (err: any) {
      toast.error(err.message || 'Failed to change subdomain');
      console.error('Change subdomain error:', err);
    }
  };

  const isValid = subdomain && !validationError && validationData?.validateSubdomain?.available;
  const extractedSubdomain = currentSubdomain?.split('.')[0] || '';

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <DialogTitle>Change .huzilerz.com domain</DialogTitle>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => onOpenChange(false)}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Your original huzilerz domain will remain visible for technical setup. You can also buy or
            connect a custom domain.
          </p>

          <div className="relative">
            <Input
              value={subdomain}
              onChange={(e) => setSubdomain(e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, ''))}
              placeholder={extractedSubdomain}
              className="pr-32"
            />
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">
              .huzilerz.com
            </span>
          </div>

          {validating && (
            <p className="text-sm text-muted-foreground">Checking availability...</p>
          )}

          {validationError && (
            <p className="text-sm text-destructive">{validationError}</p>
          )}

          {isValid && (
            <p className="text-sm text-green-600">
              {validationData?.validateSubdomain?.fullDomain} is available!
            </p>
          )}

          {changesRemaining > 0 && (
            <Alert>
              <Info className="h-4 w-4" />
              <AlertDescription>
                {changesRemaining === 1
                  ? "This is your final subdomain change"
                  : `You'll have ${changesRemaining - 1} change(s) remaining after this update`}
              </AlertDescription>
            </Alert>
          )}

          {changesRemaining === 0 && (
            <Alert variant="destructive">
              <Info className="h-4 w-4" />
              <AlertDescription>
                You have reached the maximum number of subdomain changes ({changesLimit}). Contact support if you need to change your subdomain.
              </AlertDescription>
            </Alert>
          )}

          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={changing}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={!isValid || changing || validating || changesRemaining === 0}
            >
              {changing ? 'Changing...' : 'Change domain'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
