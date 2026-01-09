import * as Types from '../../../../../../types/hosting/graphql-base';

import { TypedDocumentNode as DocumentNode } from '@graphql-typed-document-node/core';
export type SetStorefrontPasswordMutationVariables = Types.Exact<{
  input: Types.SetStorefrontPasswordInput;
}>;


export type SetStorefrontPasswordMutation = { __typename?: 'Mutation', setStorefrontPassword: { __typename?: 'SetStorefrontPassword', success: boolean | null, message: string | null, passwordEnabled: boolean | null } | null };


export const SetStorefrontPasswordDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"SetStorefrontPassword"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"SetStorefrontPasswordInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"setStorefrontPassword"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"success"}},{"kind":"Field","name":{"kind":"Name","value":"message"}},{"kind":"Field","name":{"kind":"Name","value":"passwordEnabled"}}]}}]}}]} as unknown as DocumentNode<SetStorefrontPasswordMutation, SetStorefrontPasswordMutationVariables>;