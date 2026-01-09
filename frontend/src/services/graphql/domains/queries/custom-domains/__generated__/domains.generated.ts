import * as Types from '../../../../../../types/hosting/graphql-base';

import { TypedDocumentNode as DocumentNode } from '@graphql-typed-document-node/core';
export type DomainsQueryVariables = Types.Exact<{
  workspaceId: Types.Scalars['ID']['input'];
}>;


export type DomainsQuery = { __typename?: 'Query', domains: Array<{ __typename?: 'DomainType', id: string | null, domain: string, type: string, status: string, isPrimary: boolean, managedBy: string | null, addedAt: string | null, subdomainChangesRemaining: number | null, subdomainChangesLimit: number | null } | null> | null };


export const DomainsDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"Domains"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"workspaceId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"domains"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"workspaceId"},"value":{"kind":"Variable","name":{"kind":"Name","value":"workspaceId"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"domain"}},{"kind":"Field","name":{"kind":"Name","value":"type"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"isPrimary"}},{"kind":"Field","name":{"kind":"Name","value":"managedBy"}},{"kind":"Field","name":{"kind":"Name","value":"addedAt"}},{"kind":"Field","name":{"kind":"Name","value":"subdomainChangesRemaining"}},{"kind":"Field","name":{"kind":"Name","value":"subdomainChangesLimit"}}]}}]}}]} as unknown as DocumentNode<DomainsQuery, DomainsQueryVariables>;