/**
 * Template Detail API Route
 * 
 * Production-grade API route for fetching individual template details
 * Supports both UUID and slug-based lookups
 */

import { NextRequest, NextResponse } from 'next/server';

const BACKEND_API_URL = process.env.BACKEND_API_URL || 'http://localhost:8001';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: templateId } = await params;
    
    // Exclude non-UUID routes from this handler
    if (templateId === 'discover') {
      return NextResponse.json(
        { error: 'Use /api/templates/discover endpoint' },
        { status: 404 }
      );
    }
    
    if (!templateId) {
      return NextResponse.json(
        { error: 'Template ID is required' },
        { status: 400 }
      );
    }

    // Call backend API to get template details
    const backendResponse = await fetch(
      `${BACKEND_API_URL}/api/templates/marketplace/${templateId}/`,
      {
        headers: {
          'Accept': 'application/json',
          'User-Agent': 'Huzilerz-Frontend/1.0',
        },
      }
    );

    if (!backendResponse.ok) {
      if (backendResponse.status === 404) {
        return NextResponse.json(
          { error: 'Template not found' },
          { status: 404 }
        );
      }
      
      throw new Error(`Backend API error: ${backendResponse.status}`);
    }

    const templateData = await backendResponse.json();

    // Return template data with CORS headers
    return NextResponse.json(templateData, {
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET',
        'Access-Control-Allow-Headers': 'Content-Type',
      },
    });

  } catch (error) {
    console.error('Template API Error:', error);
    
    return NextResponse.json(
      { 
        error: 'Internal server error',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}

// Handle preflight requests
export async function OPTIONS() {
  return NextResponse.json({}, {
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  });
}