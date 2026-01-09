import * as Types from '../../../../../types/notifications/graphql-base';

import { TypedDocumentNode as DocumentNode } from '@graphql-typed-document-node/core';
export type GetWorkspaceUnreadCountQueryVariables = Types.Exact<{ [key: string]: never; }>;


export type GetWorkspaceUnreadCountQuery = { __typename?: 'Query', workspaceUnreadCount: number | null };


export const GetWorkspaceUnreadCountDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"GetWorkspaceUnreadCount"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"workspaceUnreadCount"}}]}}]} as unknown as DocumentNode<GetWorkspaceUnreadCountQuery, GetWorkspaceUnreadCountQueryVariables>;