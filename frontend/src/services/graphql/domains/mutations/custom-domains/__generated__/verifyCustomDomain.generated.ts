import * as Types from '../../../../../../types/hosting/graphql-base';

import { TypedDocumentNode as DocumentNode } from '@graphql-typed-document-node/core';
export type VerifyCustomDomainMutationVariables = Types.Exact<{
  domainId: Types.Scalars['ID']['input'];
}>;


export type VerifyCustomDomainMutation = { __typename?: 'Mutation', verifyCustomDomain: { __typename?: 'VerifyCustomDomain', success: boolean | null, message: string | null, error: string | null, verified: boolean | null, domain: { __typename?: 'CustomDomainType', id: string, domain: string, status: Types.WorkspaceHostingCustomDomainStatusChoices, verifiedAt: string | null } | null } | null };


export const VerifyCustomDomainDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"VerifyCustomDomain"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"domainId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"verifyCustomDomain"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"domainId"},"value":{"kind":"Variable","name":{"kind":"Name","value":"domainId"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"success"}},{"kind":"Field","name":{"kind":"Name","value":"message"}},{"kind":"Field","name":{"kind":"Name","value":"error"}},{"kind":"Field","name":{"kind":"Name","value":"verified"}},{"kind":"Field","name":{"kind":"Name","value":"domain"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"domain"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"verifiedAt"}}]}}]}}]}}]} as unknown as DocumentNode<VerifyCustomDomainMutation, VerifyCustomDomainMutationVariables>;