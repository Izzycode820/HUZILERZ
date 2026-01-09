import * as Types from '../../../types/graphql/graphql-base';

import { TypedDocumentNode as DocumentNode } from '@graphql-typed-document-node/core';
export type CustomerLogoutMutationVariables = Types.Exact<{
  sessionToken: Types.Scalars['String']['input'];
}>;


export type CustomerLogoutMutation = { __typename: 'Mutation', customerLogout: { __typename: 'CustomerLogout', success: boolean | null, message: string | null } | null };


export const CustomerLogoutDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"CustomerLogout"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"sessionToken"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"String"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"customerLogout"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"sessionToken"},"value":{"kind":"Variable","name":{"kind":"Name","value":"sessionToken"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"success"}},{"kind":"Field","name":{"kind":"Name","value":"message"}}]}}]}}]} as unknown as DocumentNode<CustomerLogoutMutation, CustomerLogoutMutationVariables>;