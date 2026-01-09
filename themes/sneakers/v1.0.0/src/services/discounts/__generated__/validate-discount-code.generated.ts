import * as Types from '../../../types/graphql/graphql-base';

import { TypedDocumentNode as DocumentNode } from '@graphql-typed-document-node/core';
export type ValidateDiscountCodeQueryVariables = Types.Exact<{
  sessionId: Types.Scalars['String']['input'];
  discountCode: Types.Scalars['String']['input'];
}>;


export type ValidateDiscountCodeQuery = { __typename: 'Query', validateDiscountCode: { __typename: 'DiscountValidationType', valid: boolean, error: string | null, discountCode: string | null, discountName: string | null, discountType: string | null, message: string | null } | null };


export const ValidateDiscountCodeDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"ValidateDiscountCode"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"sessionId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"String"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"discountCode"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"String"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"validateDiscountCode"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"sessionId"},"value":{"kind":"Variable","name":{"kind":"Name","value":"sessionId"}}},{"kind":"Argument","name":{"kind":"Name","value":"discountCode"},"value":{"kind":"Variable","name":{"kind":"Name","value":"discountCode"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"valid"}},{"kind":"Field","name":{"kind":"Name","value":"error"}},{"kind":"Field","name":{"kind":"Name","value":"discountCode"}},{"kind":"Field","name":{"kind":"Name","value":"discountName"}},{"kind":"Field","name":{"kind":"Name","value":"discountType"}},{"kind":"Field","name":{"kind":"Name","value":"message"}}]}}]}}]} as unknown as DocumentNode<ValidateDiscountCodeQuery, ValidateDiscountCodeQueryVariables>;