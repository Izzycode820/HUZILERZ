import * as Types from '../../../../../../types/workspace/store/graphql-base';

import { TypedDocumentNode as DocumentNode } from '@graphql-typed-document-node/core';
export type CategoryPickerQueryVariables = Types.Exact<{ [key: string]: never; }>;


export type CategoryPickerQuery = { __typename?: 'Query', categories: { __typename?: 'CategoryTypeConnection', edges: Array<{ __typename?: 'CategoryTypeEdge', node: { __typename?: 'CategoryType', id: string, name: string } | null } | null> } | null };


export const CategoryPickerDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"CategoryPicker"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"categories"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"edges"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"node"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}}]}}]}}]}}]}}]} as unknown as DocumentNode<CategoryPickerQuery, CategoryPickerQueryVariables>;