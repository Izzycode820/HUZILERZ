import { CustomerDetailsContainer } from '@/components/workspace/store/customers/details';

interface CustomerDetailsPageProps {
  params: {
    id: string;
  };
}

export default function CustomerDetailsPage({ params }: CustomerDetailsPageProps) {
  return <CustomerDetailsContainer customerId={params.id} />;
}
