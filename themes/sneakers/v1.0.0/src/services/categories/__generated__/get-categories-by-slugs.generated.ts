import * as Types from '../../../types/graphql/graphql-base';

import { TypedDocumentNode as DocumentNode } from '@graphql-typed-document-node/core';
export type GetCategoriesBySlugsQueryVariables = Types.Exact<{
  slugs: Array<Types.Scalars['String']['input']> | Types.Scalars['String']['input'];
}>;


export type GetCategoriesBySlugsQuery = { __typename: 'Query', categoriesBySlugs: Array<{ __typename: 'CategoryType', id: string, name: string, slug: string, productCount: number | null, categoryImage: { __typename: 'MediaUploadType', thumbnailUrl: string | null, optimizedUrl: string | null } | null } | null> | null };


export const GetCategoriesBySlugsDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"GetCategoriesBySlugs"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"slugs"}},"type":{"kind":"NonNullType","type":{"kind":"ListType","type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"String"}}}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"categoriesBySlugs"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"slugs"},"value":{"kind":"Variable","name":{"kind":"Name","value":"slugs"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"slug"}},{"kind":"Field","name":{"kind":"Name","value":"categoryImage"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"thumbnailUrl"}},{"kind":"Field","name":{"kind":"Name","value":"optimizedUrl"}}]}},{"kind":"Field","name":{"kind":"Name","value":"productCount"}}]}}]}}]} as unknown as DocumentNode<GetCategoriesBySlugsQuery, GetCategoriesBySlugsQueryVariables>;