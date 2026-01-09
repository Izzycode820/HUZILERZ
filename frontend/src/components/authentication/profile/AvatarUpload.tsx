/**
 * Avatar Upload Component
 * Built with Shadcn/UI components for file upload
 * Supports drag & drop with proper validation
 */

'use client'

import React from 'react'
import { Upload, X, User, Loader2 } from 'lucide-react'

// Shadcn/UI Components
import { Button } from '@/components/shadcn-ui/button'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/shadcn-ui/avatar'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/shadcn-ui/card'

// Hooks
import { useAuth } from '@/hooks/authentication/useAuth'

export interface AvatarUploadProps {
  onSuccess?: (avatarUrl: string) => void
  onError?: (error: string) => void
  className?: string
  maxSize?: number // In MB
}

export function AvatarUpload({
  onSuccess,
  onError,
  className = '',
  maxSize = 5 // 5MB default
}: AvatarUploadProps) {
  const { user, userDisplayName } = useAuth()
  const [isUploading, setIsUploading] = React.useState(false)
  const [dragOver, setDragOver] = React.useState(false)
  const [preview, setPreview] = React.useState<string | null>(null)
  const fileInputRef = React.useRef<HTMLInputElement>(null)

  const validateFile = (file: File): string | null => {
    // Check file type
    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
    if (!allowedTypes.includes(file.type)) {
      return 'Please upload a valid image file (JPEG, PNG, WebP, or GIF)'
    }

    // Check file size
    const maxSizeBytes = maxSize * 1024 * 1024
    if (file.size > maxSizeBytes) {
      return `File size must be less than ${maxSize}MB`
    }

    return null
  }

  const handleFileUpload = async (file: File) => {
    const validationError = validateFile(file)
    if (validationError) {
      onError?.(validationError)
      return
    }

    try {
      setIsUploading(true)

      // Create preview
      const reader = new FileReader()
      reader.onload = (e) => {
        setPreview(e.target?.result as string)
      }
      reader.readAsDataURL(file)

      // Here you would implement the actual upload to your backend
      // For now, we'll simulate an upload
      const formData = new FormData()
      formData.append('avatar', file)

      // Simulate upload delay
      await new Promise(resolve => setTimeout(resolve, 2000))

      // Mock successful upload response
      const mockAvatarUrl = URL.createObjectURL(file)
      onSuccess?.(mockAvatarUrl)

      // TODO: Replace with actual API call
      // const response = await fetch('/api/auth/upload-avatar', {
      //   method: 'POST',
      //   body: formData,
      //   headers: {
      //     'Authorization': `Bearer ${accessToken}`
      //   }
      // })
      //
      // if (!response.ok) {
      //   throw new Error('Upload failed')
      // }
      //
      // const data = await response.json()
      // onSuccess?.(data.avatar_url)

    } catch (err: unknown) {
      const errorMessage = err.message || 'Failed to upload avatar. Please try again.'
      onError?.(errorMessage)
      setPreview(null)
    } finally {
      setIsUploading(false)
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      handleFileUpload(file)
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)

    const file = e.dataTransfer.files[0]
    if (file) {
      handleFileUpload(file)
    }
  }

  const handleRemoveAvatar = () => {
    setPreview(null)
    // TODO: Implement remove avatar API call
    onSuccess?.('')
  }

  const triggerFileSelect = () => {
    fileInputRef.current?.click()
  }

  const displayAvatar = preview || user?.avatar
  const initials = userDisplayName
    ?.split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase() || '??'

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <User className="h-5 w-5" />
          <span>Profile Picture</span>
        </CardTitle>
        <CardDescription>
          Upload a profile picture to personalize your account
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Current Avatar Display */}
        <div className="flex items-center space-x-4">
          <Avatar className="h-20 w-20">
            <AvatarImage src={displayAvatar} alt="Profile picture" />
            <AvatarFallback className="text-lg font-semibold">
              {initials}
            </AvatarFallback>
          </Avatar>

          <div className="space-y-2">
            <p className="text-sm font-medium">{userDisplayName}</p>
            <p className="text-xs text-muted-foreground">
              {user?.email}
            </p>
            {displayAvatar && (
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleRemoveAvatar}
                disabled={isUploading}
                className="text-xs"
              >
                <X className="h-3 w-3 mr-1" />
                Remove
              </Button>
            )}
          </div>
        </div>

        {/* Upload Area */}
        <div
          className={`
            border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer
            ${dragOver
              ? 'border-primary bg-primary/5'
              : 'border-muted-foreground/25 hover:border-muted-foreground/50'
            }
            ${isUploading ? 'opacity-50 pointer-events-none' : ''}
          `}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={triggerFileSelect}
        >
          {isUploading ? (
            <div className="space-y-2">
              <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary" />
              <p className="text-sm text-muted-foreground">Uploading...</p>
            </div>
          ) : (
            <div className="space-y-4">
              <Upload className="h-8 w-8 mx-auto text-muted-foreground" />
              <div className="space-y-2">
                <p className="text-sm font-medium">
                  Drop your image here, or click to browse
                </p>
                <p className="text-xs text-muted-foreground">
                  JPEG, PNG, WebP or GIF up to {maxSize}MB
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Hidden File Input */}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp,image/gif"
          onChange={handleFileSelect}
          disabled={isUploading}
          className="hidden"
        />

        {/* Upload Button */}
        <Button
          type="button"
          variant="outline"
          onClick={triggerFileSelect}
          disabled={isUploading}
          className="w-full"
        >
          {isUploading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Uploading...
            </>
          ) : (
            <>
              <Upload className="mr-2 h-4 w-4" />
              Choose file
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  )
}