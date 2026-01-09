import * as Types from '../../../../../../types/subscription/graphql-base';

import { TypedDocumentNode as DocumentNode } from '@graphql-typed-document-node/core';
export type GetBillingProfileQueryVariables = Types.Exact<{ [key: string]: never; }>;


export type GetBillingProfileQuery = { __typename?: 'Query', billingProfile: { __typename?: 'BillingProfileType', primaryPaymentMethod: string | null, userPhone: string | null } | null };


export const GetBillingProfileDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"GetBillingProfile"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"billingProfile"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"primaryPaymentMethod"}},{"kind":"Field","name":{"kind":"Name","value":"userPhone"}}]}}]}}]} as unknown as DocumentNode<GetBillingProfileQuery, GetBillingProfileQueryVariables>;