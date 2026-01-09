'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { CategoryForm, type CategoryFormData } from '@/components/workspace/store/categories/form/CategoryForm';
import { Button } from '@/components/shadcn-ui/button';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { useMutation } from '@apollo/client/react';
import { CreateCategoryDocument } from '@/services/graphql/admin-store/mutations/categories/__generated__/createCategory.generated';
import { useWorkspaceStore, workspaceSelectors } from '@/stores/authentication/workspaceStore';
import { toast } from 'sonner';

const stripHtmlTags = (html: string): string => {
  return html
    .replace(/<[^>]*>/g, '')
    .replace(/\s+/g, ' ')
    .trim();
};

export default function AddCategoryPage() {
  const router = useRouter();
  const currentWorkspace = useWorkspaceStore(workspaceSelectors.currentWorkspace);

  const [createCategory, { loading }] = useMutation(CreateCategoryDocument, {
    onCompleted: (data) => {
      if (data.createCategory?.success && data.createCategory?.category) {
        toast.success(`${data.createCategory.category.name} has been created successfully.`);
        // Navigate to categories list
        router.push(`/workspace/${currentWorkspace?.id}/store/products/categories`);
      } else {
        toast.error(data.createCategory?.error || "Failed to create category");
      }
    },
    onError: (error) => {
      toast.error(error.message || "An unexpected error occurred");
    },
  });

  const handleSubmit = async (data: CategoryFormData) => {
    await createCategory({
      variables: {
        name: data.name,
        description: data.description ? stripHtmlTags(data.description) : undefined,
        featuredMediaId: data.featuredMediaId,
        isVisible: data.isVisible,
        isFeatured: data.isFeatured,
        sortOrder: data.sortOrder,
        metaTitle: data.metaTitle || undefined,
        metaDescription: data.metaDescription ? data.metaDescription : (data.description ? stripHtmlTags(data.description) : undefined),
      },
    });
  };

  const handleSaveDraft = async (data: CategoryFormData) => {
    await createCategory({
      variables: {
        name: data.name,
        description: data.description ? stripHtmlTags(data.description) : undefined,
        featuredMediaId: data.featuredMediaId,
        isVisible: false,
        isFeatured: data.isFeatured,
        sortOrder: data.sortOrder,
        metaTitle: data.metaTitle || undefined,
        metaDescription: data.metaDescription ? data.metaDescription : (data.description ? stripHtmlTags(data.description) : undefined),
      },
    });
  };

  const handlePreview = () => {
    toast.info("Category preview coming soon!");
  };

  if (!currentWorkspace) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-muted-foreground">Loading workspace...</p>
      </div>
    );
  }

  return (
    <div className="@container/main flex flex-1 flex-col gap-2">
      <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
        {/* Header */}
        <div className="px-4 lg:px-6">
          <div className="flex items-center gap-4 mb-4">
            <Link href={`/workspace/${currentWorkspace.id}/store/categories`}>
              <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                <ArrowLeft className="h-4 w-4" />
              </Button>
            </Link>
            <h1 className="text-2xl font-bold">Add Category</h1>
          </div>
          <p className="text-muted-foreground">
            Create a new category for your store
          </p>
        </div>

        {/* Main Form */}
        <div className="px-4 lg:px-6">
          <CategoryForm
            onSubmit={handleSubmit}
            onSaveDraft={handleSaveDraft}
            onPreview={handlePreview}
            isEditing={false}
            isLoading={loading}
          />
        </div>
      </div>
    </div>
  );
}