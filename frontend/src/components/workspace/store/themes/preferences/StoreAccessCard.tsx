'use client';

import { useState } from 'react';
import { useMutation } from '@apollo/client/react';
import { useParams } from 'next/navigation';
import { Card } from '@/components/shadcn-ui/card';
import { Input } from '@/components/shadcn-ui/input';
import { Label } from '@/components/shadcn-ui/label';
import { Textarea } from '@/components/shadcn-ui/textarea';
import { Switch } from '@/components/shadcn-ui/switch';
import { Button } from '@/components/shadcn-ui/button';
import { Alert, AlertDescription } from '@/components/shadcn-ui/alert';
import { SetStorefrontPasswordDocument } from '@/services/graphql/hosting/mutations/storefront/__generated__/setStorefrontPassword.generated';
import { IconInfoCircle, IconLock } from '@tabler/icons-react';

interface StoreAccessCardProps {
  initialPassword: string | null;
  assignedDomain: string;
  initialEnabled: boolean;
  initialDescription: string | null;
}

export function StoreAccessCard({
  initialPassword,
  assignedDomain,
  initialEnabled,
  initialDescription
}: StoreAccessCardProps) {
  const params = useParams();
  const workspaceId = params?.workspace_id as string;

  const [password, setPassword] = useState(initialPassword || '');
  const [message, setMessage] = useState(initialDescription || '');
  const [enabled, setEnabled] = useState(initialEnabled || false);
  const [hasChanges, setHasChanges] = useState(false);

  const [setStorefrontPassword, { loading }] = useMutation(SetStorefrontPasswordDocument);

  // Track changes to enable save button
  const handlePasswordChange = (val: string) => {
    setPassword(val);
    setHasChanges(true);
  };

  const handleMessageChange = (val: string) => {
    setMessage(val);
    setHasChanges(true);
  };

  const handleToggle = async (checked: boolean) => {
    try {
      setEnabled(checked);
      // Auto-save on toggle for better UX (like Shopify)
      await setStorefrontPassword({
        variables: {
          input: {
            workspaceId,
            enabled: checked,
            // Don't send other fields to avoid accidental overwrites
          },
        },
      });
    } catch (error) {
      console.error('Failed to toggle password protection:', error);
      // Revert UI on error
      setEnabled(!checked);
    }
  };

  const handleSave = async () => {
    try {
      await setStorefrontPassword({
        variables: {
          input: {
            workspaceId,
            password: password || null,
            description: message || null,
            enabled: enabled, // Explicitly send current state
          },
        },
      });
      setHasChanges(false);
    } catch (error) {
      console.error('Failed to save password settings:', error);
    }
  };

  const passwordLength = password.length;
  const messageLength = message.length;

  return (
    <div className="w-full max-w-[1000px] mx-auto px-6">
      <Card className="p-6">
        <h2 className="text-base font-semibold mb-6">Store access</h2>

        <div className="space-y-5">
          {/* Password Protection Header */}
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-3">
              <IconLock className="w-5 h-5 mt-0.5 text-muted-foreground" />
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-medium">Password protection</h3>
                  <IconInfoCircle className="w-4 h-4 text-muted-foreground" />
                </div>
                <p className="text-sm text-muted-foreground mt-1">
                  Restrict access to visitors with the password
                </p>
              </div>
            </div>
            <Switch
              checked={enabled}
              onCheckedChange={handleToggle}
              disabled={loading}
              className="data-[state=checked]:bg-blue-600"
            />
          </div>

          {/* Info Alert - Only show when Disabled */}
          {!enabled && (
            <Alert className="bg-blue-500/10 dark:bg-blue-500/10 border-blue-500/20 dark:border-blue-500/20">
              <IconInfoCircle className="h-4 w-4 text-blue-600 dark:text-blue-400" />
              <AlertDescription className="ml-2 text-sm text-blue-900 dark:text-blue-300">
                To password protect your online store, enable the switch above.
              </AlertDescription>
            </Alert>
          )}

          {/* Enabled State Info */}
          {enabled && (
            <div className="bg-muted/30 p-3 rounded-md border text-sm flex items-center justify-between">
              <span className="text-muted-foreground">Preview your password page:</span>
              <a
                href={`https://${assignedDomain}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline font-medium flex items-center gap-1"
              >
                {assignedDomain} <span className="text-xs">↗</span>
              </a>
            </div>
          )}

          {/* Fields - Only enabled when protection is ON */}
          <div className={`space-y-5 transition-opacity duration-200 ${enabled ? 'opacity-100' : 'opacity-50 pointer-events-none'}`}>

            {/* Password Input */}
            <div className="space-y-2">
              <Label htmlFor="password" className="text-sm font-medium">Password</Label>
              <Input
                id="password"
                type="text"
                value={password}
                onChange={(e) => handlePasswordChange(e.target.value)}
                maxLength={100}
                placeholder="Enter password"
                disabled={!enabled}
              />
              <p className="text-xs text-muted-foreground">
                {passwordLength} of 100 characters used
              </p>
            </div>

            {/* Message to Visitors */}
            <div className="space-y-2">
              <Label htmlFor="message" className="text-sm font-medium">Message to your visitors</Label>
              <Textarea
                id="message"
                value={message}
                onChange={(e) => handleMessageChange(e.target.value)}
                maxLength={5000}
                rows={3}
                placeholder="Enter a message for your visitors"
                className="resize-none"
                disabled={!enabled}
              />
              <p className="text-xs text-muted-foreground">
                {messageLength} of 5,000 characters used
              </p>
            </div>

            {/* Save Button */}
            <div className="flex justify-end pt-2">
              <Button
                onClick={handleSave}
                disabled={!hasChanges || loading || !enabled}
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                {loading ? 'Saving...' : 'Save changes'}
              </Button>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
