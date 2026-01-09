import * as Types from '../../../types/graphql/graphql-base';

import { TypedDocumentNode as DocumentNode } from '@graphql-typed-document-node/core';
export type TrackOrderQueryVariables = Types.Exact<{
  orderNumber: Types.Scalars['String']['input'];
  phone: Types.Scalars['String']['input'];
}>;


export type TrackOrderQuery = { __typename: 'Query', trackOrder: { __typename: 'OrderTrackingType', orderNumber: string | null, status: string | null, totalAmount: string | null, createdAt: string | null, trackingNumber: string | null } | null };


export const TrackOrderDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"TrackOrder"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"orderNumber"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"String"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"phone"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"String"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"trackOrder"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"orderNumber"},"value":{"kind":"Variable","name":{"kind":"Name","value":"orderNumber"}}},{"kind":"Argument","name":{"kind":"Name","value":"phone"},"value":{"kind":"Variable","name":{"kind":"Name","value":"phone"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"orderNumber"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"totalAmount"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"trackingNumber"}}]}}]}}]} as unknown as DocumentNode<TrackOrderQuery, TrackOrderQueryVariables>;