import * as Types from '../../../../../../types/hosting/graphql-base';

import { TypedDocumentNode as DocumentNode } from '@graphql-typed-document-node/core';
export type PurchaseStatusQueryVariables = Types.Exact<{
  purchaseId: Types.Scalars['ID']['input'];
}>;


export type PurchaseStatusQuery = { __typename?: 'Query', purchaseStatus: { __typename?: 'DomainPurchaseStatusType', id: string, domainName: string, status: string, priceFcfa: string, paymentStatus: Types.WorkspaceHostingDomainPurchasePaymentStatusChoices, errorMessage: string, createdAt: string } | null };


export const PurchaseStatusDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"PurchaseStatus"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"purchaseId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"purchaseStatus"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"purchaseId"},"value":{"kind":"Variable","name":{"kind":"Name","value":"purchaseId"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"domainName"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"priceFcfa"}},{"kind":"Field","name":{"kind":"Name","value":"paymentStatus"}},{"kind":"Field","name":{"kind":"Name","value":"errorMessage"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}}]}}]}}]} as unknown as DocumentNode<PurchaseStatusQuery, PurchaseStatusQueryVariables>;