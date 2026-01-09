import * as Types from '../../../../../../types/workspace/store/graphql-base';

import { TypedDocumentNode as DocumentNode } from '@graphql-typed-document-node/core';
export type DeleteDiscountMutationVariables = Types.Exact<{
  discountId: Types.Scalars['String']['input'];
}>;


export type DeleteDiscountMutation = { __typename?: 'Mutation', deleteDiscount: { __typename?: 'DeleteDiscount', success: boolean | null, message: string | null, error: string | null } | null };


export const DeleteDiscountDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"DeleteDiscount"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"discountId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"String"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"deleteDiscount"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"discountId"},"value":{"kind":"Variable","name":{"kind":"Name","value":"discountId"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"success"}},{"kind":"Field","name":{"kind":"Name","value":"message"}},{"kind":"Field","name":{"kind":"Name","value":"error"}}]}}]}}]} as unknown as DocumentNode<DeleteDiscountMutation, DeleteDiscountMutationVariables>;