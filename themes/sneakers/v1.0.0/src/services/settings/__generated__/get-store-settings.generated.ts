import * as Types from '../../../types/graphql/graphql-base';

import { TypedDocumentNode as DocumentNode } from '@graphql-typed-document-node/core';
export type GetStoreSettingsQueryVariables = Types.Exact<{ [key: string]: never; }>;


export type GetStoreSettingsQuery = { __typename: 'Query', storeSettings: { __typename: 'StoreSettingsType', storeName: string | null, storeDescription: string | null, whatsappNumber: string | null, phoneNumber: string | null, supportEmail: string | null, currency: string | null } | null };


export const GetStoreSettingsDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"GetStoreSettings"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"storeSettings"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"storeName"}},{"kind":"Field","name":{"kind":"Name","value":"storeDescription"}},{"kind":"Field","name":{"kind":"Name","value":"whatsappNumber"}},{"kind":"Field","name":{"kind":"Name","value":"phoneNumber"}},{"kind":"Field","name":{"kind":"Name","value":"supportEmail"}},{"kind":"Field","name":{"kind":"Name","value":"currency"}}]}}]}}]} as unknown as DocumentNode<GetStoreSettingsQuery, GetStoreSettingsQueryVariables>;