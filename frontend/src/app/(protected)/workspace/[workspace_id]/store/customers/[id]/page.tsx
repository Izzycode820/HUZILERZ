import { CustomerDetailsContainer } from '@/components/workspace/store/customers/details';

interface CustomerDetailsPageProps {
  params: Promise<{
    id: string;
  }>;
}

export default async function CustomerDetailsPage({ params }: CustomerDetailsPageProps) {
  const { id } = await params;
  return <CustomerDetailsContainer customerId={id} />;
}
