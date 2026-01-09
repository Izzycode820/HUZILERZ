'use client'

import { Sparkles } from 'lucide-react'

export function GenerateTab() {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      <div className="bg-primary/10 rounded-full p-6 mb-6">
        <Sparkles className="h-12 w-12 text-primary" />
      </div>

      <h3 className="text-lg font-semibold mb-2">AI Image Generation</h3>
      <p className="text-sm text-muted-foreground max-w-md mb-4">
        Generate product images using AI. Create stunning visuals from text descriptions.
      </p>

      <div className="inline-flex items-center gap-2 px-4 py-2 bg-muted rounded-full">
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
        </span>
        <span className="text-xs font-medium">Coming Soon</span>
      </div>

      <div className="mt-8 grid grid-cols-2 gap-4 text-left max-w-md">
        <div className="border rounded-lg p-3 space-y-1">
          <p className="text-xs font-medium">Text-to-Image</p>
          <p className="text-xs text-muted-foreground">
            Generate images from descriptions
          </p>
        </div>
        <div className="border rounded-lg p-3 space-y-1">
          <p className="text-xs font-medium">Background Removal</p>
          <p className="text-xs text-muted-foreground">
            Auto remove & replace backgrounds
          </p>
        </div>
        <div className="border rounded-lg p-3 space-y-1">
          <p className="text-xs font-medium">Image Enhancement</p>
          <p className="text-xs text-muted-foreground">
            Upscale & improve quality
          </p>
        </div>
        <div className="border rounded-lg p-3 space-y-1">
          <p className="text-xs font-medium">Variations</p>
          <p className="text-xs text-muted-foreground">
            Create multiple angles
          </p>
        </div>
      </div>
    </div>
  )
}
