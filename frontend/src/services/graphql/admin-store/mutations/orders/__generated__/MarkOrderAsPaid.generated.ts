import * as Types from '../../../../../../types/workspace/store/graphql-base';

import { TypedDocumentNode as DocumentNode } from '@graphql-typed-document-node/core';
export type MarkOrderAsPaidMutationVariables = Types.Exact<{
  orderId: Types.Scalars['String']['input'];
}>;


export type MarkOrderAsPaidMutation = { __typename?: 'Mutation', markOrderAsPaid: { __typename?: 'MarkOrderAsPaid', success: boolean | null, message: string | null, error: string | null, order: { __typename?: 'OrderType', id: string, paymentStatus: Types.WorkspaceStoreOrderPaymentStatusChoices, status: Types.WorkspaceStoreOrderStatusChoices, canMarkAsPaid: boolean | null } | null } | null };


export const MarkOrderAsPaidDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"MarkOrderAsPaid"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"orderId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"String"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"markOrderAsPaid"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"orderId"},"value":{"kind":"Variable","name":{"kind":"Name","value":"orderId"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"success"}},{"kind":"Field","name":{"kind":"Name","value":"message"}},{"kind":"Field","name":{"kind":"Name","value":"error"}},{"kind":"Field","name":{"kind":"Name","value":"order"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"paymentStatus"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"canMarkAsPaid"}}]}}]}}]}}]} as unknown as DocumentNode<MarkOrderAsPaidMutation, MarkOrderAsPaidMutationVariables>;