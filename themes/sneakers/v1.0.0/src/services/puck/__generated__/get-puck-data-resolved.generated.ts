import * as Types from '../../../types/graphql/graphql-base';

import { TypedDocumentNode as DocumentNode } from '@graphql-typed-document-node/core';
export type GetPuckDataResolvedQueryVariables = Types.Exact<{ [key: string]: never; }>;


export type GetPuckDataResolvedQuery = { __typename: 'Query', publicPuckDataResolved: { __typename: 'PuckDataResolvedResponse', success: boolean | null, message: string | null, data: unknown | null } | null };


export const GetPuckDataResolvedDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"GetPuckDataResolved"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"publicPuckDataResolved"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"success"}},{"kind":"Field","name":{"kind":"Name","value":"message"}},{"kind":"Field","name":{"kind":"Name","value":"data"}}]}}]}}]} as unknown as DocumentNode<GetPuckDataResolvedQuery, GetPuckDataResolvedQueryVariables>;