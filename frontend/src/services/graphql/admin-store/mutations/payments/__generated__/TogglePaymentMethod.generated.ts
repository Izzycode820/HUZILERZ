import * as Types from '../../../../../../types/workspace/store/graphql-base';

import { TypedDocumentNode as DocumentNode } from '@graphql-typed-document-node/core';
export type TogglePaymentMethodMutationVariables = Types.Exact<{
  methodId: Types.Scalars['ID']['input'];
  enabled: Types.Scalars['Boolean']['input'];
}>;


export type TogglePaymentMethodMutation = { __typename?: 'Mutation', togglePaymentMethod: { __typename?: 'TogglePaymentMethod', success: boolean | null, message: string | null, error: string | null, paymentMethod: { __typename?: 'MerchantPaymentMethodType', id: string, enabled: boolean } | null } | null };


export const TogglePaymentMethodDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"TogglePaymentMethod"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"methodId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"enabled"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"Boolean"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"togglePaymentMethod"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"methodId"},"value":{"kind":"Variable","name":{"kind":"Name","value":"methodId"}}},{"kind":"Argument","name":{"kind":"Name","value":"enabled"},"value":{"kind":"Variable","name":{"kind":"Name","value":"enabled"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"success"}},{"kind":"Field","name":{"kind":"Name","value":"message"}},{"kind":"Field","name":{"kind":"Name","value":"error"}},{"kind":"Field","name":{"kind":"Name","value":"paymentMethod"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"enabled"}}]}}]}}]}}]} as unknown as DocumentNode<TogglePaymentMethodMutation, TogglePaymentMethodMutationVariables>;