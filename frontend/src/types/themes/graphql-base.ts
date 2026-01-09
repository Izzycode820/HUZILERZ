export type Maybe<T> = T | null;
export type InputMaybe<T> = Maybe<T>;
export type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
export type MakeOptional<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]?: Maybe<T[SubKey]> };
export type MakeMaybe<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]: Maybe<T[SubKey]> };
export type MakeEmpty<T extends { [key: string]: unknown }, K extends keyof T> = { [_ in K]?: never };
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
/** All built-in and custom scalars, mapped to their actual values */
export interface Scalars {
  ID: { input: string; output: string; }
  String: { input: string; output: string; }
  Boolean: { input: boolean; output: boolean; }
  Int: { input: number; output: number; }
  Float: { input: number; output: number; }
  DateTime: { input: string; output: string; }
  Decimal: { input: string; output: string; }
  JSONString: { input: any; output: any; }
}

/**
 * Add theme to user's library (clone from theme store)
 *
 * Shopify pattern: "Use theme" button in theme store
 * Creates draft customization with cloned puck data
 */
export interface AddTheme {
  __typename?: 'AddTheme';
  customization?: Maybe<ThemeCustomizationType>;
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Delete theme from library
 *
 * Shopify pattern: Permanent deletion (no archive)
 * Cannot delete active theme - must publish another first
 */
export interface DeleteTheme {
  __typename?: 'DeleteTheme';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Duplicate theme for experimentation
 *
 * Shopify pattern: Copy theme to try variations
 * Creates new draft with copied puck data
 */
export interface DuplicateTheme {
  __typename?: 'DuplicateTheme';
  customization?: Maybe<ThemeCustomizationType>;
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Feature category with items list
 * Used for nested features structure
 */
export interface FeatureCategoryType {
  __typename?: 'FeatureCategoryType';
  category?: Maybe<Scalars['String']['output']>;
  items?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
}

/**
 * Theme mutations (all require authentication + workspace scoping)
 *
 * - addTheme: Clone theme to library
 * - updateThemeCustomization: Save Puck edits
 * - publishTheme: Make theme live
 * - unpublishTheme: Take theme offline
 * - deleteTheme: Remove from library
 * - duplicateTheme: Copy for experimentation
 * - renameTheme: Change theme name
 */
export interface Mutation {
  __typename?: 'Mutation';
  /**
   * Add theme to user's library (clone from theme store)
   *
   * Shopify pattern: "Use theme" button in theme store
   * Creates draft customization with cloned puck data
   */
  addTheme?: Maybe<AddTheme>;
  /**
   * Delete theme from library
   *
   * Shopify pattern: Permanent deletion (no archive)
   * Cannot delete active theme - must publish another first
   */
  deleteTheme?: Maybe<DeleteTheme>;
  /**
   * Duplicate theme for experimentation
   *
   * Shopify pattern: Copy theme to try variations
   * Creates new draft with copied puck data
   */
  duplicateTheme?: Maybe<DuplicateTheme>;
  /**
   * Publish theme (make it live on workspace)
   *
   * Shopify pattern: Only one published theme at a time
   * Auto-unpublishes any other active theme
   */
  publishTheme?: Maybe<PublishTheme>;
  /**
   * Rename theme in library
   *
   * User-friendly labels for theme organization
   */
  renameTheme?: Maybe<RenameTheme>;
  /**
   * Unpublish theme (take it offline)
   *
   * Workspace will have no active theme until another is published
   * Use case: Maintenance mode or switching themes
   */
  unpublishTheme?: Maybe<UnpublishTheme>;
  /**
   * Update theme customization (save Puck editor changes)
   *
   * Auto-saves from Puck editor every 30s or manual save
   * Updates puck_data and/or puck_config
   */
  updateThemeCustomization?: Maybe<UpdateThemeCustomization>;
}


/**
 * Theme mutations (all require authentication + workspace scoping)
 *
 * - addTheme: Clone theme to library
 * - updateThemeCustomization: Save Puck edits
 * - publishTheme: Make theme live
 * - unpublishTheme: Take theme offline
 * - deleteTheme: Remove from library
 * - duplicateTheme: Copy for experimentation
 * - renameTheme: Change theme name
 */
export interface MutationAddThemeArgs {
  themeSlug: Scalars['String']['input'];
  workspaceId: Scalars['ID']['input'];
}


/**
 * Theme mutations (all require authentication + workspace scoping)
 *
 * - addTheme: Clone theme to library
 * - updateThemeCustomization: Save Puck edits
 * - publishTheme: Make theme live
 * - unpublishTheme: Take theme offline
 * - deleteTheme: Remove from library
 * - duplicateTheme: Copy for experimentation
 * - renameTheme: Change theme name
 */
export interface MutationDeleteThemeArgs {
  id: Scalars['ID']['input'];
}


/**
 * Theme mutations (all require authentication + workspace scoping)
 *
 * - addTheme: Clone theme to library
 * - updateThemeCustomization: Save Puck edits
 * - publishTheme: Make theme live
 * - unpublishTheme: Take theme offline
 * - deleteTheme: Remove from library
 * - duplicateTheme: Copy for experimentation
 * - renameTheme: Change theme name
 */
export interface MutationDuplicateThemeArgs {
  id: Scalars['ID']['input'];
  newName?: InputMaybe<Scalars['String']['input']>;
}


/**
 * Theme mutations (all require authentication + workspace scoping)
 *
 * - addTheme: Clone theme to library
 * - updateThemeCustomization: Save Puck edits
 * - publishTheme: Make theme live
 * - unpublishTheme: Take theme offline
 * - deleteTheme: Remove from library
 * - duplicateTheme: Copy for experimentation
 * - renameTheme: Change theme name
 */
export interface MutationPublishThemeArgs {
  id: Scalars['ID']['input'];
}


/**
 * Theme mutations (all require authentication + workspace scoping)
 *
 * - addTheme: Clone theme to library
 * - updateThemeCustomization: Save Puck edits
 * - publishTheme: Make theme live
 * - unpublishTheme: Take theme offline
 * - deleteTheme: Remove from library
 * - duplicateTheme: Copy for experimentation
 * - renameTheme: Change theme name
 */
export interface MutationRenameThemeArgs {
  id: Scalars['ID']['input'];
  name: Scalars['String']['input'];
}


/**
 * Theme mutations (all require authentication + workspace scoping)
 *
 * - addTheme: Clone theme to library
 * - updateThemeCustomization: Save Puck edits
 * - publishTheme: Make theme live
 * - unpublishTheme: Take theme offline
 * - deleteTheme: Remove from library
 * - duplicateTheme: Copy for experimentation
 * - renameTheme: Change theme name
 */
export interface MutationUnpublishThemeArgs {
  id: Scalars['ID']['input'];
}


/**
 * Theme mutations (all require authentication + workspace scoping)
 *
 * - addTheme: Clone theme to library
 * - updateThemeCustomization: Save Puck edits
 * - publishTheme: Make theme live
 * - unpublishTheme: Take theme offline
 * - deleteTheme: Remove from library
 * - duplicateTheme: Copy for experimentation
 * - renameTheme: Change theme name
 */
export interface MutationUpdateThemeCustomizationArgs {
  id: Scalars['ID']['input'];
  input: UpdateThemeCustomizationInput;
}

/** An object with an ID */
export interface Node {
  /** The ID of the object */
  id: Scalars['ID']['output'];
}

/** The Relay compliant `PageInfo` type, containing data necessary to paginate this connection. */
export interface PageInfo {
  __typename?: 'PageInfo';
  /** When paginating forwards, the cursor to continue. */
  endCursor?: Maybe<Scalars['String']['output']>;
  /** When paginating forwards, are there more items? */
  hasNextPage: Scalars['Boolean']['output'];
  /** When paginating backwards, are there more items? */
  hasPreviousPage: Scalars['Boolean']['output'];
  /** When paginating backwards, the cursor to continue. */
  startCursor?: Maybe<Scalars['String']['output']>;
}

/**
 * Publish theme (make it live on workspace)
 *
 * Shopify pattern: Only one published theme at a time
 * Auto-unpublishes any other active theme
 */
export interface PublishTheme {
  __typename?: 'PublishTheme';
  customization?: Maybe<ThemeCustomizationType>;
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/** Response type for public puck data query */
export interface PuckDataResponse {
  __typename?: 'PuckDataResponse';
  data?: Maybe<Scalars['JSONString']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Combined theme queries
 *
 * Public queries (no auth):
 * - themes: Browse theme store
 * - themeDetails: View single theme
 * - publicPuckData: Fetch puck data for storefront (X-Store-Hostname header)
 *
 * Authenticated queries (requires workspace):
 * - myThemes: User's theme library
 * - themeCustomization: Get customization for editor
 * - activeTheme: Currently published theme
 */
export interface Query {
  __typename?: 'Query';
  /** Get currently published theme for workspace */
  activeTheme?: Maybe<ThemeCustomizationType>;
  /** Get all themes in user's library (published + drafts) */
  myThemes?: Maybe<Array<Maybe<ThemeCustomizationType>>>;
  /** Fetch active theme's puck data for storefront (uses X-Store-Hostname header) */
  publicPuckData?: Maybe<PuckDataResponse>;
  /** Get specific theme customization for Puck editor */
  themeCustomization?: Maybe<ThemeCustomizationType>;
  /** Get detailed theme information by slug (PUBLIC) */
  themeDetails?: Maybe<ThemeDetailsType>;
  /** Browse theme store with pagination and filtering (PUBLIC) */
  themes?: Maybe<ThemeTypeConnection>;
}


/**
 * Combined theme queries
 *
 * Public queries (no auth):
 * - themes: Browse theme store
 * - themeDetails: View single theme
 * - publicPuckData: Fetch puck data for storefront (X-Store-Hostname header)
 *
 * Authenticated queries (requires workspace):
 * - myThemes: User's theme library
 * - themeCustomization: Get customization for editor
 * - activeTheme: Currently published theme
 */
export interface QueryActiveThemeArgs {
  workspaceId: Scalars['ID']['input'];
}


/**
 * Combined theme queries
 *
 * Public queries (no auth):
 * - themes: Browse theme store
 * - themeDetails: View single theme
 * - publicPuckData: Fetch puck data for storefront (X-Store-Hostname header)
 *
 * Authenticated queries (requires workspace):
 * - myThemes: User's theme library
 * - themeCustomization: Get customization for editor
 * - activeTheme: Currently published theme
 */
export interface QueryMyThemesArgs {
  workspaceId: Scalars['ID']['input'];
}


/**
 * Combined theme queries
 *
 * Public queries (no auth):
 * - themes: Browse theme store
 * - themeDetails: View single theme
 * - publicPuckData: Fetch puck data for storefront (X-Store-Hostname header)
 *
 * Authenticated queries (requires workspace):
 * - myThemes: User's theme library
 * - themeCustomization: Get customization for editor
 * - activeTheme: Currently published theme
 */
export interface QueryThemeCustomizationArgs {
  id: Scalars['ID']['input'];
}


/**
 * Combined theme queries
 *
 * Public queries (no auth):
 * - themes: Browse theme store
 * - themeDetails: View single theme
 * - publicPuckData: Fetch puck data for storefront (X-Store-Hostname header)
 *
 * Authenticated queries (requires workspace):
 * - myThemes: User's theme library
 * - themeCustomization: Get customization for editor
 * - activeTheme: Currently published theme
 */
export interface QueryThemeDetailsArgs {
  slug: Scalars['String']['input'];
}


/**
 * Combined theme queries
 *
 * Public queries (no auth):
 * - themes: Browse theme store
 * - themeDetails: View single theme
 * - publicPuckData: Fetch puck data for storefront (X-Store-Hostname header)
 *
 * Authenticated queries (requires workspace):
 * - myThemes: User's theme library
 * - themeCustomization: Get customization for editor
 * - activeTheme: Currently published theme
 */
export interface QueryThemesArgs {
  after?: InputMaybe<Scalars['String']['input']>;
  before?: InputMaybe<Scalars['String']['input']>;
  first?: InputMaybe<Scalars['Int']['input']>;
  last?: InputMaybe<Scalars['Int']['input']>;
  name_Icontains?: InputMaybe<Scalars['String']['input']>;
  offset?: InputMaybe<Scalars['Int']['input']>;
  priceTier?: InputMaybe<Scalars['String']['input']>;
  slug?: InputMaybe<Scalars['String']['input']>;
  templateType?: InputMaybe<Scalars['String']['input']>;
}

/**
 * Rename theme in library
 *
 * User-friendly labels for theme organization
 */
export interface RenameTheme {
  __typename?: 'RenameTheme';
  customization?: Maybe<ThemeCustomizationType>;
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Showcase section with title, description, and image
 * Used in theme details page
 */
export interface ShowcaseSectionType {
  __typename?: 'ShowcaseSectionType';
  description?: Maybe<Scalars['String']['output']>;
  image?: Maybe<Scalars['String']['output']>;
  title?: Maybe<Scalars['String']['output']>;
}

/**
 * User's theme customization in their library
 *
 * Contains user's puck data/config for the Puck editor
 * Workspace-scoped - only accessible to workspace owner
 */
export interface ThemeCustomizationType extends Node {
  __typename?: 'ThemeCustomizationType';
  canDelete?: Maybe<Scalars['Boolean']['output']>;
  createdAt: Scalars['DateTime']['output'];
  id: Scalars['ID']['output'];
  /** Whether this theme is currently published and live on the workspace */
  isActive: Scalars['Boolean']['output'];
  isDraft?: Maybe<Scalars['Boolean']['output']>;
  /** Whether the published storefront is password protected */
  isPasswordProtected?: Maybe<Scalars['Boolean']['output']>;
  isPublished?: Maybe<Scalars['Boolean']['output']>;
  /** When customization was last modified */
  lastEditedAt: Scalars['DateTime']['output'];
  /** When this customization was last published to production */
  publishedAt?: Maybe<Scalars['DateTime']['output']>;
  /** User customizations stored as Puck configuration */
  puckConfig: Scalars['JSONString']['output'];
  /** Current page layout and content data for Puck editor */
  puckData: Scalars['JSONString']['output'];
  /** Current password for password-protected storefront (for merchant to share) */
  storefrontPassword?: Maybe<Scalars['String']['output']>;
  /** Master template being customized */
  template: ThemeDetailsType;
  /** User-friendly name for this theme (can be renamed) */
  themeName: Scalars['String']['output'];
  themeSlug?: Maybe<Scalars['String']['output']>;
}

/**
 * Detailed theme type for single theme view
 *
 * Contains full metadata for decision-making
 * Still NO puck data (user gets that after adding to library)
 */
export interface ThemeDetailsType {
  __typename?: 'ThemeDetailsType';
  /** Number of active workspaces using this template */
  activeUsageCount: Scalars['Int']['output'];
  /** Template author or creator */
  author: Scalars['String']['output'];
  /** Technology compatibility requirements (nextjs, react, etc.) */
  compatibility: Scalars['JSONString']['output'];
  createdAt: Scalars['DateTime']['output'];
  /** Live demo URL for previewing the template */
  demoUrl: Scalars['String']['output'];
  /** Detailed description of the template */
  description: Scalars['String']['output'];
  /** Number of times this template has been downloaded */
  downloadCount: Scalars['Int']['output'];
  features?: Maybe<Array<Maybe<FeatureCategoryType>>>;
  id: Scalars['ID']['output'];
  isFree?: Maybe<Scalars['Boolean']['output']>;
  isPaid?: Maybe<Scalars['Boolean']['output']>;
  /** Template license type */
  license: Scalars['String']['output'];
  /** Unique name for the template */
  name: Scalars['String']['output'];
  /** Preview image URL from CDN */
  previewImage: Scalars['String']['output'];
  /** Price in FCFA for paid/exclusive templates */
  priceAmount?: Maybe<Scalars['Decimal']['output']>;
  /** Pricing category for the template */
  priceTier: ThemeTemplatePriceTierChoices;
  showcaseSections?: Maybe<Array<Maybe<ShowcaseSectionType>>>;
  /** URL-friendly version of the name */
  slug: Scalars['String']['output'];
  /** Current status of the template */
  status: ThemeTemplateStatusChoices;
  /** Tags for categorization and search */
  tags: Scalars['JSONString']['output'];
  /** Type of business this template is designed for */
  templateType: ThemeTemplateTemplateTypeChoices;
  updatedAt: Scalars['DateTime']['output'];
  /** Current version of the template */
  version: Scalars['String']['output'];
  /** Number of times this template has been viewed */
  viewCount: Scalars['Int']['output'];
  /** List of compatible workspace types (e.g., ['store', 'services']) */
  workspaceTypes: Scalars['JSONString']['output'];
}

/** An enumeration. */
export enum ThemeTemplatePriceTierChoices {
  /** Exclusive */
  Exclusive = 'EXCLUSIVE',
  /** Free */
  Free = 'FREE',
  /** Paid */
  Paid = 'PAID'
}

/** An enumeration. */
export enum ThemeTemplateStatusChoices {
  /** Active */
  Active = 'ACTIVE',
  /** Deprecated */
  Deprecated = 'DEPRECATED',
  /** Draft */
  Draft = 'DRAFT'
}

/** An enumeration. */
export enum ThemeTemplateTemplateTypeChoices {
  /** Blog */
  Blog = 'BLOG',
  /** E-commerce */
  Ecommerce = 'ECOMMERCE',
  /** Restaurant */
  Restaurant = 'RESTAURANT',
  /** Services */
  Services = 'SERVICES'
}

/**
 * Public theme type for theme store listing
 *
 * Contains light metadata for browsing
 * NO puck data (that's only for user customizations)
 */
export interface ThemeType extends Node {
  __typename?: 'ThemeType';
  /** Number of active workspaces using this template */
  activeUsageCount: Scalars['Int']['output'];
  createdAt: Scalars['DateTime']['output'];
  /** Live demo URL for previewing the template */
  demoUrl: Scalars['String']['output'];
  /** Detailed description of the template */
  description: Scalars['String']['output'];
  /** Number of times this template has been downloaded */
  downloadCount: Scalars['Int']['output'];
  id: Scalars['ID']['output'];
  /** Unique name for the template */
  name: Scalars['String']['output'];
  /** Preview image URL from CDN */
  previewImage: Scalars['String']['output'];
  /** Price in FCFA for paid/exclusive templates */
  priceAmount?: Maybe<Scalars['Decimal']['output']>;
  /** Pricing category for the template */
  priceTier: ThemeTemplatePriceTierChoices;
  /** URL-friendly version of the name */
  slug: Scalars['String']['output'];
  /** Current status of the template */
  status: ThemeTemplateStatusChoices;
  /** Type of business this template is designed for */
  templateType: ThemeTemplateTemplateTypeChoices;
  updatedAt: Scalars['DateTime']['output'];
  /** Current version of the template */
  version: Scalars['String']['output'];
  /** Number of times this template has been viewed */
  viewCount: Scalars['Int']['output'];
}

export interface ThemeTypeConnection {
  __typename?: 'ThemeTypeConnection';
  /** Contains the nodes in this connection. */
  edges: Array<Maybe<ThemeTypeEdge>>;
  /** Pagination data for this connection. */
  pageInfo: PageInfo;
  totalCount?: Maybe<Scalars['Int']['output']>;
}

/** A Relay edge containing a `ThemeType` and its cursor. */
export interface ThemeTypeEdge {
  __typename?: 'ThemeTypeEdge';
  /** A cursor for use in pagination */
  cursor: Scalars['String']['output'];
  /** The item at the end of the edge */
  node?: Maybe<ThemeType>;
}

/**
 * Unpublish theme (take it offline)
 *
 * Workspace will have no active theme until another is published
 * Use case: Maintenance mode or switching themes
 */
export interface UnpublishTheme {
  __typename?: 'UnpublishTheme';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Update theme customization (save Puck editor changes)
 *
 * Auto-saves from Puck editor every 30s or manual save
 * Updates puck_data and/or puck_config
 */
export interface UpdateThemeCustomization {
  __typename?: 'UpdateThemeCustomization';
  customization?: Maybe<ThemeCustomizationType>;
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
}

/**
 * Input for updating theme customization
 *
 * Updates user's puck data and config from Puck editor
 * Both fields optional - update only what changed
 */
export interface UpdateThemeCustomizationInput {
  /** User's customized Puck config (component settings) */
  puckConfig?: InputMaybe<Scalars['JSONString']['input']>;
  /** User's customized Puck data (page layout) */
  puckData?: InputMaybe<Scalars['JSONString']['input']>;
}
