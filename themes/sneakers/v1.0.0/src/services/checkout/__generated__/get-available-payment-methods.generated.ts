import * as Types from '../../../types/graphql/graphql-base';

import { TypedDocumentNode as DocumentNode } from '@graphql-typed-document-node/core';
export type GetAvailablePaymentMethodsQueryVariables = Types.Exact<{ [key: string]: never; }>;


export type GetAvailablePaymentMethodsQuery = { __typename: 'Query', availablePaymentMethods: Array<{ __typename: 'AvailablePaymentMethodType', provider: string, displayName: string, checkoutUrl: string | null, description: string | null } | null> | null };


export const GetAvailablePaymentMethodsDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"GetAvailablePaymentMethods"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"availablePaymentMethods"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"provider"}},{"kind":"Field","name":{"kind":"Name","value":"displayName"}},{"kind":"Field","name":{"kind":"Name","value":"checkoutUrl"}},{"kind":"Field","name":{"kind":"Name","value":"description"}}]}}]}}]} as unknown as DocumentNode<GetAvailablePaymentMethodsQuery, GetAvailablePaymentMethodsQueryVariables>;