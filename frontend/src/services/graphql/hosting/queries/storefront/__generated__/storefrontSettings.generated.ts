import * as Types from '../../../../../../types/hosting/graphql-base';

import { TypedDocumentNode as DocumentNode } from '@graphql-typed-document-node/core';
export type StorefrontSettingsQueryVariables = Types.Exact<{
  workspaceId: Types.Scalars['ID']['input'];
}>;


export type StorefrontSettingsQuery = { __typename?: 'Query', storefrontSettings: { __typename?: 'StorefrontSettingsType', password: string | null, passwordEnabled: boolean, passwordDescription: string | null, seoTitle: string, seoDescription: string | null, seoKeywords: string | null, seoImageUrl: string | null, assignedDomain: string, previewUrl: string | null, siteName: string | null } | null };


export const StorefrontSettingsDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"StorefrontSettings"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"workspaceId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"storefrontSettings"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"workspaceId"},"value":{"kind":"Variable","name":{"kind":"Name","value":"workspaceId"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"password"}},{"kind":"Field","name":{"kind":"Name","value":"passwordEnabled"}},{"kind":"Field","name":{"kind":"Name","value":"passwordDescription"}},{"kind":"Field","name":{"kind":"Name","value":"seoTitle"}},{"kind":"Field","name":{"kind":"Name","value":"seoDescription"}},{"kind":"Field","name":{"kind":"Name","value":"seoKeywords"}},{"kind":"Field","name":{"kind":"Name","value":"seoImageUrl"}},{"kind":"Field","name":{"kind":"Name","value":"assignedDomain"}},{"kind":"Field","name":{"kind":"Name","value":"previewUrl"}},{"kind":"Field","name":{"kind":"Name","value":"siteName"}}]}}]}}]} as unknown as DocumentNode<StorefrontSettingsQuery, StorefrontSettingsQueryVariables>;