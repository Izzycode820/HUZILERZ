import { ProductView } from '@/components/product/ProductView';

interface PageProps {
  params: Promise<{
    slug: string;
  }>;
}

export default async function ProductPage({ params }: PageProps) {
  const { slug } = await params;
  return <ProductView slug={slug} />;
}
