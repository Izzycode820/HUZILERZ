import * as Types from '../../../../../../types/hosting/graphql-base';

import { TypedDocumentNode as DocumentNode } from '@graphql-typed-document-node/core';
export type UpdateStorefrontSeoMutationVariables = Types.Exact<{
  input: Types.UpdateStorefrontSeoInput;
}>;


export type UpdateStorefrontSeoMutation = { __typename?: 'Mutation', updateStorefrontSeo: { __typename?: 'UpdateStorefrontSEO', success: boolean | null, message: string | null, warnings: Array<string | null> | null, seoSettings: { __typename?: 'SEOSettingsType', title: string | null, description: string | null, keywords: string | null, imageUrl: string | null } | null } | null };


export const UpdateStorefrontSeoDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"UpdateStorefrontSEO"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"UpdateStorefrontSEOInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"updateStorefrontSeo"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"success"}},{"kind":"Field","name":{"kind":"Name","value":"message"}},{"kind":"Field","name":{"kind":"Name","value":"warnings"}},{"kind":"Field","name":{"kind":"Name","value":"seoSettings"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"title"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"keywords"}},{"kind":"Field","name":{"kind":"Name","value":"imageUrl"}}]}}]}}]}}]} as unknown as DocumentNode<UpdateStorefrontSeoMutation, UpdateStorefrontSeoMutationVariables>;