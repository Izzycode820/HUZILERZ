"use client";

import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@apollo/client/react";
import { GetProductDocument } from "@/services/graphql/admin-store/queries/products/__generated__/GetProduct.generated";
import { ProductPreviewContainer } from "@/components/workspace/store/products/preview";
import { Button } from "@/components/shadcn-ui/button";
import { ArrowLeft, Eye } from "lucide-react";
import { Skeleton } from "@/components/shadcn-ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/shadcn-ui/alert";

export default function ProductPreviewPage() {
  const params = useParams();
  const router = useRouter();
  const productId = params.id as string;
  const workspaceId = params.workspace_id as string;

  const { data, loading, error } = useQuery(GetProductDocument, {
    variables: { id: productId },
    skip: !productId,
  });

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Header Skeleton */}
        <div className="mb-8">
          <Skeleton className="h-10 w-48 mb-4" />
          <Skeleton className="h-6 w-96" />
        </div>

        {/* Content Skeleton */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12">
          <div>
            <Skeleton className="aspect-square w-full rounded-lg" />
            <div className="grid grid-cols-4 gap-2 mt-4">
              {[1, 2, 3, 4].map((i) => (
                <Skeleton key={i} className="aspect-square rounded-md" />
              ))}
            </div>
          </div>
          <div className="space-y-6">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-6 w-3/4" />
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-32 w-full" />
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <Alert variant="destructive">
          <AlertTitle>Error loading product</AlertTitle>
          <AlertDescription>
            {error.message || "Failed to load product. Please try again."}
          </AlertDescription>
        </Alert>
        <Button
          variant="outline"
          className="mt-4"
          onClick={() => router.back()}
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Go Back
        </Button>
      </div>
    );
  }

  if (!data?.product) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <Alert>
          <AlertTitle>Product not found</AlertTitle>
          <AlertDescription>
            The product you're looking for doesn't exist or has been deleted.
          </AlertDescription>
        </Alert>
        <Button
          variant="outline"
          className="mt-4"
          onClick={() => router.back()}
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Go Back
        </Button>
      </div>
    );
  }

  return (
    <div>
      {/* Preview Header */}
      <div className="border-b bg-muted/50">
        <div className="container mx-auto px-4 py-4 max-w-7xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => router.back()}
              >
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back
              </Button>
              <div className="flex items-center gap-2">
                <Eye className="h-5 w-5 text-muted-foreground" />
                <div>
                  <h1 className="text-lg font-semibold">Product Preview</h1>
                  <p className="text-sm text-muted-foreground">
                    This is how your product will appear to customers
                  </p>
                </div>
              </div>
            </div>
            <Button
              onClick={() =>
                router.push(
                  `/(protected)/workspace/${workspaceId}/store/products/${productId}/edit`
                )
              }
            >
              Edit Product
            </Button>
          </div>
        </div>
      </div>

      {/* Product Preview Content */}
      <ProductPreviewContainer product={data.product} />
    </div>
  );
}
