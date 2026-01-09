import * as Types from '../../../../../../types/workspace/store/graphql-base';

import { TypedDocumentNode as DocumentNode } from '@graphql-typed-document-node/core';
export type BulkUpdateOrderStatusMutationVariables = Types.Exact<{
  bulkData: Types.BulkStatusUpdateInput;
}>;


export type BulkUpdateOrderStatusMutation = { __typename?: 'Mutation', bulkUpdateOrderStatus: { __typename?: 'BulkUpdateOrderStatus', success: boolean | null, totalUpdates: number | null, successfulUpdates: number | null, failedUpdates: Array<any | null> | null, message: string | null, error: string | null } | null };


export const BulkUpdateOrderStatusDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"BulkUpdateOrderStatus"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"bulkData"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"BulkStatusUpdateInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"bulkUpdateOrderStatus"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"bulkData"},"value":{"kind":"Variable","name":{"kind":"Name","value":"bulkData"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"success"}},{"kind":"Field","name":{"kind":"Name","value":"totalUpdates"}},{"kind":"Field","name":{"kind":"Name","value":"successfulUpdates"}},{"kind":"Field","name":{"kind":"Name","value":"failedUpdates"}},{"kind":"Field","name":{"kind":"Name","value":"message"}},{"kind":"Field","name":{"kind":"Name","value":"error"}}]}}]}}]} as unknown as DocumentNode<BulkUpdateOrderStatusMutation, BulkUpdateOrderStatusMutationVariables>;