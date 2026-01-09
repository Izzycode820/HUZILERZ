'use client'

import { useCallback, useState } from 'react'
import { Upload } from 'lucide-react'
import type { UploadProgress, MediaType } from './types'

interface UploadZoneProps {
  /** Allowed media types */
  allowedTypes?: MediaType[]

  /** Maximum file size in MB */
  maxSizeMB?: number

  /** Whether multiple files allowed */
  multiple?: boolean

  /** File selection handler */
  onFilesSelected: (files: File[]) => void

  /** Current uploads in progress */
  uploads?: UploadProgress[]
}

export function UploadZone({
  allowedTypes = ['image', 'video', '3d_model'],
  maxSizeMB = 50,
  multiple = true,
  onFilesSelected,
  uploads = [],
}: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false)

  // Get accept attribute for file input
  const getAcceptAttribute = () => {
    const accepts: string[] = []
    if (allowedTypes.includes('image')) {
      accepts.push('image/*')
    }
    if (allowedTypes.includes('video')) {
      accepts.push('video/*')
    }
    if (allowedTypes.includes('3d_model')) {
      accepts.push('.glb', '.gltf', '.obj', '.fbx', '.usdz')
    }
    return accepts.join(',')
  }

  // Validate and handle file selection
  const handleFiles = useCallback(
    (files: FileList | null) => {
      if (!files) return

      const validFiles: File[] = []
      const maxSize = maxSizeMB * 1024 * 1024

      Array.from(files).forEach((file) => {
        // Check size
        if (file.size > maxSize) {
          alert(`File "${file.name}" is too large. Maximum size is ${maxSizeMB}MB.`)
          return
        }

        validFiles.push(file)
      })

      if (validFiles.length > 0) {
        onFilesSelected(validFiles)
      }
    },
    [maxSizeMB, onFilesSelected]
  )

  // Drag & drop handlers
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setIsDragging(false)
      handleFiles(e.dataTransfer.files)
    },
    [handleFiles]
  )

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      handleFiles(e.target.files)
    },
    [handleFiles]
  )

  return (
    <div>
      {/* Compact Drop Zone - Shopify style */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-4 text-center transition-colors max-w-md mx-auto ${
          isDragging
            ? 'border-primary bg-primary/5'
            : 'border-muted-foreground/25 hover:border-muted-foreground/40'
        }`}
      >
        <Upload className="mx-auto h-8 w-8 text-muted-foreground mb-2" />
        <p className="text-sm text-muted-foreground mb-2">
          Drag and drop or{' '}
          <button
            type="button"
            onClick={() => document.getElementById('file-upload')?.click()}
            className="text-primary hover:underline font-medium"
          >
            browse files
          </button>
        </p>
        <p className="text-xs text-muted-foreground">
          {allowedTypes.includes('image') && 'Images, '}
          {allowedTypes.includes('video') && 'Videos, '}
          {allowedTypes.includes('3d_model') && '3D Models '}
          (max {maxSizeMB}MB)
        </p>

        <input
          type="file"
          id="file-upload"
          multiple={multiple}
          accept={getAcceptAttribute()}
          onChange={handleFileInput}
          className="hidden"
        />
      </div>
    </div>
  )
}
