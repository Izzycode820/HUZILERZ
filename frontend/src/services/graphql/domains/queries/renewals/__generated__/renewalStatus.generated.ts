import * as Types from '../../../../../../types/hosting/graphql-base';

import { TypedDocumentNode as DocumentNode } from '@graphql-typed-document-node/core';
export type RenewalStatusQueryVariables = Types.Exact<{
  renewalId: Types.Scalars['ID']['input'];
}>;


export type RenewalStatusQuery = { __typename?: 'Query', renewalStatus: { __typename?: 'DomainRenewalStatusType', id: string, domainName: string, status: string, renewalPriceFcfa: string, paymentStatus: string | null, previousExpiryDate: string, newExpiryDate: string | null, renewedAt: string | null, errorMessage: string, createdAt: string } | null };


export const RenewalStatusDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"RenewalStatus"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"renewalId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"renewalStatus"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"renewalId"},"value":{"kind":"Variable","name":{"kind":"Name","value":"renewalId"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"domainName"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"renewalPriceFcfa"}},{"kind":"Field","name":{"kind":"Name","value":"paymentStatus"}},{"kind":"Field","name":{"kind":"Name","value":"previousExpiryDate"}},{"kind":"Field","name":{"kind":"Name","value":"newExpiryDate"}},{"kind":"Field","name":{"kind":"Name","value":"renewedAt"}},{"kind":"Field","name":{"kind":"Name","value":"errorMessage"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}}]}}]}}]} as unknown as DocumentNode<RenewalStatusQuery, RenewalStatusQueryVariables>;