import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';
import { createHash } from 'crypto';

interface TemplateMetadata {
  id?: string;
  frontend_id?: string;
  name: string;
  version: string;
  category: string;
  description: string;
  features: string[];
  pages: Array<{
    id: string;
    name: string;
    description: string;
  }>;
  editableFields: {
    [key: string]: any;
  };
  subscription_tier?: string;
  template_type?: string;
}

interface DiscoveryResponse {
  success: boolean;
  templates: TemplateMetadata[];
  total_found: number;
  stats: {
    total_scanned: number;
    valid_templates: number;
    errors: number;
  };
  error?: string;
}

/**
 * Generate deterministic frontend ID from template metadata
 * Same template always produces the same ID for consistent tracking
 */
function generateFrontendId(name: string, category: string): string {
  const identifier = `${category}-${name}`.toLowerCase().replace(/\s+/g, '-');
  const hash = createHash('sha256').update(identifier).digest('hex');
  
  // Format as UUID for consistency with backend
  return [
    hash.slice(0, 8),
    hash.slice(8, 12),
    '4' + hash.slice(13, 16),
    hash.slice(16, 20),
    hash.slice(20, 32)
  ].join('-');
}

export async function GET(request: NextRequest): Promise<NextResponse<DiscoveryResponse>> {
  try {
    const stats = {
      total_scanned: 0,
      valid_templates: 0,
      errors: 0
    };

    const templates: TemplateMetadata[] = [];

    // Path to templates directory
    const templatesPath = path.join(process.cwd(), 'src', 'lib', 'templates');
    
    if (!fs.existsSync(templatesPath)) {
      return NextResponse.json({
        success: true,
        templates: [],
        total_found: 0,
        stats,
        error: 'Templates directory not found'
      });
    }

    // Scan template categories (free, premium, pro)
    const categories = ['free', 'premium', 'pro'];
    
    for (const category of categories) {
      const categoryPath = path.join(templatesPath, category);
      
      if (!fs.existsSync(categoryPath)) {
        continue;
      }

      const templateDirs = fs.readdirSync(categoryPath, { withFileTypes: true })
        .filter(dirent => dirent.isDirectory())
        .map(dirent => dirent.name);

      for (const templateDir of templateDirs) {
        stats.total_scanned++;
        
        try {
          const metadataPath = path.join(categoryPath, templateDir, 'metadata.json');
          
          if (!fs.existsSync(metadataPath)) {
            stats.errors++;
            continue;
          }

          const metadataContent = fs.readFileSync(metadataPath, 'utf-8');
          const metadata: TemplateMetadata = JSON.parse(metadataContent);

          // Generate stable frontend identifier for template tracking
          metadata.frontend_id = generateFrontendId(metadata.name, metadata.category);
          
          // Add component path resolution data
          (metadata as any).component_path = `${category}/${templateDir}/v1.0.0`;
          (metadata as any).config_file = "puck.config.tsx";
          
          // Load actual Puck data from puck.data.ts file
          const puckDataPath = path.join(categoryPath, templateDir, 'v1.0.0', 'puck.data.ts');
          let puckData = { content: [], root: { props: {} }, zones: {} };
          
          if (fs.existsSync(puckDataPath)) {
            try {
              // Dynamically import the puck data file
              const puckModule = require(puckDataPath.replace(/\\/g, '/'));
              puckData = puckModule.initialData || puckData;
            } catch (error) {
              console.warn(`Failed to load puck data for ${templateDir}:`, error);
              // Fallback: try to parse manually
              try {
                const puckContent = fs.readFileSync(puckDataPath, 'utf-8');
                const cleanContent = puckContent
                  .replace(/import.*?;/g, '') // Remove imports
                  .replace(/export const initialData.*?=/g, 'const initialData =') // Clean export
                  .replace(/type:\s*'/g, "type: '"); // Ensure consistent quotes
                
                // Find the data object
                const match = cleanContent.match(/const initialData\s*=\s*({[\s\S]*?});?\s*$/);
                if (match) {
                  puckData = Function('"use strict"; return (' + match[1] + ')')();
                }
              } catch (fallbackError) {
                console.warn(`Fallback parsing failed for ${templateDir}:`, fallbackError);
              }
            }
          }
          
          // Add puck data to metadata
          (metadata as any).puck_data = puckData;
          
          // Enrich metadata with subscription tier and template type
          metadata.subscription_tier = category;
          metadata.template_type = metadata.category || 'ecommerce';
          
          // Remove any existing ID since backend creates database primary keys
          delete metadata.id;

          templates.push(metadata);
          stats.valid_templates++;
        } catch (error) {
          console.error(`Error processing template ${templateDir}:`, error);
          stats.errors++;
        }
      }
    }

    return NextResponse.json({
      success: true,
      templates,
      total_found: templates.length,
      stats
    });

  } catch (error) {
    console.error('Template discovery error:', error);
    return NextResponse.json({
      success: false,
      templates: [],
      total_found: 0,
      stats: { total_scanned: 0, valid_templates: 0, errors: 1 },
      error: 'Internal server error'
    }, { status: 500 });
  }
}