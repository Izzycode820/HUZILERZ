import * as Types from '../../../types/graphql/graphql-base';

import { TypedDocumentNode as DocumentNode } from '@graphql-typed-document-node/core';
export type CreateCodOrderMutationVariables = Types.Exact<{
  sessionId: Types.Scalars['String']['input'];
  customerInfo: Types.CustomerInfoInput;
  shippingRegion: Types.Scalars['String']['input'];
}>;


export type CreateCodOrderMutation = { __typename: 'Mutation', createCodOrder: { __typename: 'CreateCODOrder', success: boolean | null, orderId: string | null, orderNumber: string | null, message: string | null, error: string | null } | null };


export const CreateCodOrderDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"CreateCodOrder"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"sessionId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"String"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"customerInfo"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"CustomerInfoInput"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"shippingRegion"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"String"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"createCodOrder"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"ObjectValue","fields":[{"kind":"ObjectField","name":{"kind":"Name","value":"sessionId"},"value":{"kind":"Variable","name":{"kind":"Name","value":"sessionId"}}},{"kind":"ObjectField","name":{"kind":"Name","value":"customerInfo"},"value":{"kind":"Variable","name":{"kind":"Name","value":"customerInfo"}}},{"kind":"ObjectField","name":{"kind":"Name","value":"shippingRegion"},"value":{"kind":"Variable","name":{"kind":"Name","value":"shippingRegion"}}}]}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"success"}},{"kind":"Field","name":{"kind":"Name","value":"orderId"}},{"kind":"Field","name":{"kind":"Name","value":"orderNumber"}},{"kind":"Field","name":{"kind":"Name","value":"message"}},{"kind":"Field","name":{"kind":"Name","value":"error"}}]}}]}}]} as unknown as DocumentNode<CreateCodOrderMutation, CreateCodOrderMutationVariables>;