import * as Types from '../../../../../../types/themes/graphql-base';

import { TypedDocumentNode as DocumentNode } from '@graphql-typed-document-node/core';
export type ThemeCustomizationQueryVariables = Types.Exact<{
  id: Types.Scalars['ID']['input'];
}>;


export type ThemeCustomizationQuery = { __typename?: 'Query', themeCustomization: { __typename?: 'ThemeCustomizationType', id: string, themeName: string, themeSlug: string | null, isActive: boolean, puckConfig: any, puckData: any, template: { __typename?: 'ThemeDetailsType', id: string, name: string, slug: string } } | null };


export const ThemeCustomizationDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"ThemeCustomization"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"themeCustomization"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"themeName"}},{"kind":"Field","name":{"kind":"Name","value":"themeSlug"}},{"kind":"Field","name":{"kind":"Name","value":"isActive"}},{"kind":"Field","name":{"kind":"Name","value":"puckConfig"}},{"kind":"Field","name":{"kind":"Name","value":"puckData"}},{"kind":"Field","name":{"kind":"Name","value":"template"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"slug"}}]}}]}}]}}]} as unknown as DocumentNode<ThemeCustomizationQuery, ThemeCustomizationQueryVariables>;