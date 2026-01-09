import * as Types from '../../../../../../types/hosting/graphql-base';

import { TypedDocumentNode as DocumentNode } from '@graphql-typed-document-node/core';
export type SubdomainSuggestionsQueryVariables = Types.Exact<{
  baseName: Types.Scalars['String']['input'];
  limit?: Types.InputMaybe<Types.Scalars['Int']['input']>;
}>;


export type SubdomainSuggestionsQuery = { __typename?: 'Query', subdomainSuggestions: Array<{ __typename?: 'SubdomainSuggestionType', subdomain: string, available: boolean, fullDomain: string } | null> | null };


export const SubdomainSuggestionsDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"SubdomainSuggestions"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"baseName"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"String"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"limit"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"Int"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"subdomainSuggestions"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"baseName"},"value":{"kind":"Variable","name":{"kind":"Name","value":"baseName"}}},{"kind":"Argument","name":{"kind":"Name","value":"limit"},"value":{"kind":"Variable","name":{"kind":"Name","value":"limit"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"subdomain"}},{"kind":"Field","name":{"kind":"Name","value":"available"}},{"kind":"Field","name":{"kind":"Name","value":"fullDomain"}}]}}]}}]} as unknown as DocumentNode<SubdomainSuggestionsQuery, SubdomainSuggestionsQueryVariables>;