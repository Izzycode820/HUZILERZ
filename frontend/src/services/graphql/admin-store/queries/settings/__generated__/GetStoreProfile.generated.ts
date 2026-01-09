import * as Types from '../../../../../../types/workspace/store/graphql-base';

import { TypedDocumentNode as DocumentNode } from '@graphql-typed-document-node/core';
export type GetStoreProfileQueryVariables = Types.Exact<{ [key: string]: never; }>;


export type GetStoreProfileQuery = { __typename?: 'Query', storeProfile: { __typename?: 'StoreProfileType', id: string, storeName: string, storeDescription: string, storeEmail: string, supportEmail: string, phoneNumber: string, whatsappNumber: string, currency: Types.WorkspaceStoreStoreProfileCurrencyChoices, timezone: Types.WorkspaceStoreStoreProfileTimezoneChoices, createdAt: string, updatedAt: string } | null };


export const GetStoreProfileDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"GetStoreProfile"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"storeProfile"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"storeName"}},{"kind":"Field","name":{"kind":"Name","value":"storeDescription"}},{"kind":"Field","name":{"kind":"Name","value":"storeEmail"}},{"kind":"Field","name":{"kind":"Name","value":"supportEmail"}},{"kind":"Field","name":{"kind":"Name","value":"phoneNumber"}},{"kind":"Field","name":{"kind":"Name","value":"whatsappNumber"}},{"kind":"Field","name":{"kind":"Name","value":"currency"}},{"kind":"Field","name":{"kind":"Name","value":"timezone"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]}}]} as unknown as DocumentNode<GetStoreProfileQuery, GetStoreProfileQueryVariables>;