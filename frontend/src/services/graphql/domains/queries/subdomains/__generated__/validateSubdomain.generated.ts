import * as Types from '../../../../../../types/hosting/graphql-base';

import { TypedDocumentNode as DocumentNode } from '@graphql-typed-document-node/core';
export type ValidateSubdomainQueryVariables = Types.Exact<{
  subdomain: Types.Scalars['String']['input'];
}>;


export type ValidateSubdomainQuery = { __typename?: 'Query', validateSubdomain: { __typename?: 'SubdomainValidationType', available: boolean, subdomain: string | null, fullDomain: string | null, errors: Array<string | null> | null } | null };


export const ValidateSubdomainDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"ValidateSubdomain"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"subdomain"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"String"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"validateSubdomain"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"subdomain"},"value":{"kind":"Variable","name":{"kind":"Name","value":"subdomain"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"available"}},{"kind":"Field","name":{"kind":"Name","value":"subdomain"}},{"kind":"Field","name":{"kind":"Name","value":"fullDomain"}},{"kind":"Field","name":{"kind":"Name","value":"errors"}}]}}]}}]} as unknown as DocumentNode<ValidateSubdomainQuery, ValidateSubdomainQueryVariables>;