import { CSSProperties, ReactNode } from 'react';

export interface Rectangle {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface EditingConstraints {
  maxLength?: number;
  allowedFormats?: string[];
  requiredAspectRatio?: number;
  colorSchemeRestrictions?: boolean;
  minHeight?: number;
  maxHeight?: number;
  allowedImageTypes?: string[];
  preventDeletion?: boolean;
}

export type ComponentType = 'text' | 'image' | 'button' | 'section' | 'container' | 'heading' | 'paragraph' | 'link';
export type BusinessPurpose = 'store-name' | 'hero-text' | 'product-grid' | 'contact-info' | 'description' | 'price' | 'cta-button';

export interface EditableComponent {
  id: string;
  type: ComponentType;
  content: any;
  styles: CSSProperties;
  bounds?: Rectangle;
  editable: boolean;
  selected: boolean;
  metadata: {
    businessPurpose: BusinessPurpose;
    displayName: string;
    constraints?: EditingConstraints;
    parentId?: string;
    childIds?: string[];
  };
}

export interface EditingState {
  selectedComponentId: string | null;
  hoveredComponentId: string | null;
  editingComponentId: string | null;
  components: Map<string, EditableComponent>;
  isEditing: boolean;
  hasChanges: boolean;
}

export interface EditingAction {
  type: 'SELECT_COMPONENT' | 'HOVER_COMPONENT' | 'START_EDITING' | 'STOP_EDITING' | 'UPDATE_CONTENT' | 'UPDATE_STYLES' | 'CLEAR_SELECTION';
  payload?: any;
}

export interface LayoutConfig {
  containerMaxWidth: string;
  spacing: {
    section: string;
    element: string;
  };
  breakpoints: {
    mobile: string;
    tablet: string;
    desktop: string;
  };
}

export interface ThemeConfig {
  colors: {
    primary: string;
    secondary: string;
    accent: string;
    text: string;
    background: string;
    border: string;
  };
  fonts: {
    primary: string;
    secondary: string;
  };
  borderRadius: string;
  shadows: {
    small: string;
    medium: string;
    large: string;
  };
}

export interface EditableTemplate {
  id: string;
  name: string;
  components: EditableComponent[];
  layout: LayoutConfig;
  theme: ThemeConfig;
  businessType: 'ecommerce' | 'restaurant' | 'services' | 'portfolio';
  version: string;
  lastModified: string;
}

export interface EditorSettings {
  showBounds: boolean;
  snapToGrid: boolean;
  gridSize: number;
  showGuides: boolean;
  autoSave: boolean;
  autoSaveInterval: number;
}

export interface EditingProps {
  component: EditableComponent;
  isSelected: boolean;
  isHovered: boolean;
  isEditing: boolean;
  onSelect: (componentId: string) => void;
  onHover: (componentId: string | null) => void;
  onStartEditing: (componentId: string) => void;
  onStopEditing: () => void;
  onUpdateContent: (componentId: string, content: any) => void;
  onUpdateStyles: (componentId: string, styles: CSSProperties) => void;
  children?: ReactNode;
}

export interface SelectionBounds {
  top: number;
  left: number;
  width: number;
  height: number;
  visible: boolean;
}