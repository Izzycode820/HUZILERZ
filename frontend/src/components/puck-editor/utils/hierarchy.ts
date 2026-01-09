// Placeholder constants - to be replaced with actual theme config
const SECTION_COMPONENTS: any[] = [];
const BLOCK_COMPONENTS_BY_SECTION: Record<string, any[]> = {};

export function getAllowedBlocks(selectedNode: any) {
  if (!selectedNode) return [];

  if (selectedNode.type === 'body') {
    return SECTION_COMPONENTS;
  }

  if (selectedNode.type === 'section') {
    return BLOCK_COMPONENTS_BY_SECTION[selectedNode.component] || [];
  }

  return [];
}

// Helper functions for hierarchy enforcement
export function canAddChild(parentType: string, childType: string): boolean {
  // Implement hierarchy rules
  // Header/Footer: limited blocks
  // Body: only Sections allowed at root
  // Blocks: only allowed inside Sections
  // No arbitrary nesting
  return true;
}

export function getNodeChildren(nodeId: string, data: any): any[] {
  // Extract children from puck data based on nodeId
  return [];
}