import * as Types from '../../../../../../types/subscription/graphql-base';

import { TypedDocumentNode as DocumentNode } from '@graphql-typed-document-node/core';
export type GetBillingOverviewQueryVariables = Types.Exact<{ [key: string]: never; }>;


export type GetBillingOverviewQuery = { __typename?: 'Query', billingOverview: { __typename?: 'BillingOverviewType', upcomingBillAmount: number | null, nextBillDate: string | null, daysUntilBill: number | null, lastPaymentMethod: string | null, lastPaymentPhoneNumber: string | null } | null };


export const GetBillingOverviewDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"GetBillingOverview"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"billingOverview"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"upcomingBillAmount"}},{"kind":"Field","name":{"kind":"Name","value":"nextBillDate"}},{"kind":"Field","name":{"kind":"Name","value":"daysUntilBill"}},{"kind":"Field","name":{"kind":"Name","value":"lastPaymentMethod"}},{"kind":"Field","name":{"kind":"Name","value":"lastPaymentPhoneNumber"}}]}}]}}]} as unknown as DocumentNode<GetBillingOverviewQuery, GetBillingOverviewQueryVariables>;