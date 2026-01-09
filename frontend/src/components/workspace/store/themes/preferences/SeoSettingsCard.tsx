'use client';

import { useState } from 'react';
import { useMutation } from '@apollo/client/react';
import { useParams } from 'next/navigation';
import { Card } from '@/components/shadcn-ui/card';
import { Input } from '@/components/shadcn-ui/input';
import { Label } from '@/components/shadcn-ui/label';
import { Textarea } from '@/components/shadcn-ui/textarea';
import { Button } from '@/components/shadcn-ui/button';
import { UpdateStorefrontSeoDocument } from '@/services/graphql/hosting/mutations/storefront/__generated__/updateStorefrontSEO.generated';
import { IconInfoCircle } from '@tabler/icons-react';

interface SeoSettingsCardProps {
  initialSeoTitle?: string | null;
  initialSeoDescription?: string | null;
  initialSeoImageUrl?: string | null;
  assignedDomain: string;
}

export function SeoSettingsCard({
  initialSeoTitle,
  initialSeoDescription,
  initialSeoImageUrl,
  assignedDomain
}: SeoSettingsCardProps) {
  const params = useParams();
  const workspaceId = params?.workspace_id as string;

  const [title, setTitle] = useState(initialSeoTitle || '');
  const [description, setDescription] = useState(initialSeoDescription || '');
  const [imageUrl, setImageUrl] = useState(initialSeoImageUrl || '');
  const [hasChanges, setHasChanges] = useState(false);

  const [updateSeo, { loading }] = useMutation(UpdateStorefrontSeoDocument);

  const handleTitleChange = (val: string) => {
    setTitle(val);
    setHasChanges(true);
  };

  const handleDescriptionChange = (val: string) => {
    setDescription(val);
    setHasChanges(true);
  };

  const handleSave = async () => {
    try {
      await updateSeo({
        variables: {
          input: {
            workspaceId,
            seoTitle: title || null,
            seoDescription: description || null,
            seoImageUrl: imageUrl || null,
          },
        },
      });
      setHasChanges(false);
    } catch (error) {
      console.error('Failed to save SEO settings:', error);
    }
  };

  const titleLength = title.length;
  const descriptionLength = description.length;

  return (
    <div className="w-full max-w-[1000px] mx-auto px-6">
      <Card className="p-6">
        <div className="flex items-center gap-2 mb-6">
          <h2 className="text-base font-semibold">Social sharing image and SEO</h2>
          <IconInfoCircle className="w-4 h-4 text-muted-foreground" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-[340px_1fr] gap-6">
          {/* Left Side - Image Upload and Preview */}
          <div className="space-y-4">
            <div className="bg-muted/30 border border-dashed border-border rounded-md h-44 flex flex-col items-center justify-center">
              <Button variant="outline" size="sm">
                Add image
              </Button>
              <p className="text-xs text-muted-foreground mt-2">
                Recommended: 1200 x 628 px
              </p>
            </div>

            {/* Preview Card - Subtle gray background */}
            <div className="border border-border rounded-md p-4 bg-muted/20">
              <p className="text-xs text-muted-foreground uppercase mb-1 tracking-wide">
                {assignedDomain || 'yourdomain.myshopify.com'}
              </p>
              <h3 className="font-semibold text-sm mb-1 text-foreground">
                {title || assignedDomain || 'yourdomain.myshopify.com'}
              </h3>
              <p className="text-xs text-muted-foreground">
                {description || 'My Store'}
              </p>
            </div>
          </div>

          {/* Right Side - Form Fields */}
          <div className="space-y-5">
            {/* Home Page Title */}
            <div className="space-y-2">
              <Label htmlFor="title" className="text-sm font-medium">Home page title</Label>
              <Input
                id="title"
                type="text"
                value={title}
                onChange={(e) => handleTitleChange(e.target.value)}
                maxLength={70}
                placeholder={assignedDomain || ''}
              />
              <p className="text-xs text-muted-foreground">
                {titleLength} of 70 characters used
              </p>
            </div>

            {/* Meta Description */}
            <div className="space-y-2">
              <Label htmlFor="description" className="text-sm font-medium">Meta description</Label>
              <Textarea
                id="description"
                value={description}
                onChange={(e) => handleDescriptionChange(e.target.value)}
                maxLength={320}
                rows={5}
                placeholder="Enter a description to be shown on search engines like Google"
                className="resize-none"
              />
              <p className="text-xs text-muted-foreground">
                {descriptionLength} of 320 characters used
              </p>
            </div>

            {/* Save Button */}
            <div className="flex justify-end pt-2">
              <Button
                onClick={handleSave}
                disabled={!hasChanges || loading}
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
