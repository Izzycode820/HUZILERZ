'use client'

import { useState } from 'react'
import { Input } from '@/components/shadcn-ui/input'
import { Button } from '@/components/shadcn-ui/button'
import { Label } from '@/components/shadcn-ui/label'
import { useMutation } from '@apollo/client/react'
import { Loader2, Check, AlertCircle } from 'lucide-react'
import type { MediaItem } from '../types'
import { UploadMediaFromUrlDocument } from '@/services/graphql/admin-store/mutations/media/__generated__/UploadMediaFromUrl.generated'
import { MedialibMediaUploadMediaTypeChoices } from '@/types/workspace/store/graphql-base'

// Map backend enum to our MediaType
function mapMediaType(backendType: MedialibMediaUploadMediaTypeChoices): 'image' | 'video' | '3d_model' {
  switch (backendType) {
    case MedialibMediaUploadMediaTypeChoices.Image:
      return 'image'
    case MedialibMediaUploadMediaTypeChoices.Video:
      return 'video'
    case MedialibMediaUploadMediaTypeChoices.A_3DModel:
      return '3d_model'
    default:
      return 'image'
  }
}

interface UrlTabProps {
  onUploadComplete: (item: MediaItem) => void
}

export function UrlTab({ onUploadComplete }: UrlTabProps) {
  const [url, setUrl] = useState('')
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [error, setError] = useState('')

  const [uploadFromUrl] = useMutation(UploadMediaFromUrlDocument)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!url.trim()) {
      setError('Please enter a URL')
      return
    }

    setStatus('loading')
    setError('')

    try {
      const { data } = await uploadFromUrl({
        variables: { url: url.trim() },
      })

      if (!data?.uploadMediaFromUrl?.success || !data.uploadMediaFromUrl.upload) {
        throw new Error(data?.uploadMediaFromUrl?.error || 'Upload failed')
      }

      const upload = data.uploadMediaFromUrl.upload

      const mediaItem: MediaItem = {
        uploadId: upload.id,
        url: upload.url || '',
        type: mapMediaType(upload.mediaType),
        filename: upload.originalFilename,
        fileSize: Number(upload.fileSize),
        width: upload.width || undefined,
        height: upload.height || undefined,
        uploadedAt: upload.uploadedAt,
        mimeType: upload.mimeType,
        status: upload.status,
        // Include optimized image URLs (from backend)
        thumbnailUrl: upload.thumbnailUrl || undefined,
        optimizedUrl: upload.optimizedUrl || undefined,
      }

      onUploadComplete(mediaItem)
      setStatus('success')
      setUrl('')

      // Reset status after 2 seconds
      setTimeout(() => setStatus('idle'), 2000)
    } catch (err) {
      setStatus('error')
      setError(err instanceof Error ? err.message : 'Failed to upload from URL')
    }
  }

  return (
    <div className="space-y-4">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="media-url">Media URL</Label>
          <Input
            id="media-url"
            type="url"
            placeholder="https://example.com/image.jpg"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={status === 'loading'}
          />
          <p className="text-xs text-muted-foreground">
            Enter the URL of an image, video, or 3D model file
          </p>
        </div>

        <Button
          type="submit"
          disabled={status === 'loading' || !url.trim()}
          className="w-full"
        >
          {status === 'loading' ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Downloading...
            </>
          ) : status === 'success' ? (
            <>
              <Check className="mr-2 h-4 w-4" />
              Uploaded
            </>
          ) : (
            'Add from URL'
          )}
        </Button>

        {error && (
          <div className="flex items-center gap-2 text-sm text-destructive">
            <AlertCircle className="h-4 w-4" />
            {error}
          </div>
        )}
      </form>

      <div className="border-t pt-4">
        <p className="text-sm font-medium mb-2">Supported sources:</p>
        <ul className="text-xs text-muted-foreground space-y-1">
          <li>• Direct image URLs (.jpg, .png, .gif, .webp)</li>
          <li>• Video URLs (.mp4, .webm, .mov)</li>
          <li>• 3D model URLs (.glb, .gltf)</li>
          <li>• Most public URLs with direct file access</li>
        </ul>
      </div>
    </div>
  )
}
