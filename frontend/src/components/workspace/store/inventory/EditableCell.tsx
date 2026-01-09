'use client'

import { useState, useEffect, useRef, KeyboardEvent } from 'react'
import { Input } from '@/components/shadcn-ui/input'
import { cn } from '@/lib/utils'

interface EditableCellProps {
  value: number | null
  onSave: (value: number) => Promise<void>
  disabled?: boolean
  min?: number
  max?: number
  placeholder?: string
  className?: string
}

export function EditableCell({
  value,
  onSave,
  disabled = false,
  min = 0,
  max,
  placeholder = '0',
  className
}: EditableCellProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editValue, setEditValue] = useState(String(value ?? ''))
  const [isSaving, setIsSaving] = useState(false)
  const [hasError, setHasError] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  // Update editValue when value prop changes (from external updates)
  useEffect(() => {
    if (!isEditing) {
      setEditValue(String(value ?? ''))
    }
  }, [value, isEditing])

  // Focus input when entering edit mode
  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus()
      inputRef.current.select()
    }
  }, [isEditing])

  const handleClick = () => {
    if (!disabled && !isSaving) {
      setIsEditing(true)
    }
  }

  const handleSave = async () => {
    const numValue = parseInt(editValue, 10)

    // Validation
    if (isNaN(numValue)) {
      setHasError(true)
      return
    }

    if (min !== undefined && numValue < min) {
      setHasError(true)
      return
    }

    if (max !== undefined && numValue > max) {
      setHasError(true)
      return
    }

    // Skip if value hasn't changed
    if (numValue === (value ?? 0)) {
      setIsEditing(false)
      setHasError(false)
      return
    }

    setHasError(false)
    setIsSaving(true)

    try {
      await onSave(numValue)
      setIsEditing(false)
    } catch (error) {
      console.error('Failed to save:', error)
      setHasError(true)
    } finally {
      setIsSaving(false)
    }
  }

  const handleCancel = () => {
    setEditValue(String(value ?? ''))
    setIsEditing(false)
    setHasError(false)
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleSave()
    } else if (e.key === 'Escape') {
      e.preventDefault()
      handleCancel()
    }
  }

  const handleBlur = () => {
    // Save on blur
    if (isEditing && !hasError) {
      handleSave()
    }
  }

  if (isEditing) {
    return (
      <div className="relative">
        <Input
          ref={inputRef}
          type="number"
          value={editValue}
          onChange={(e) => {
            setEditValue(e.target.value)
            setHasError(false)
          }}
          onKeyDown={handleKeyDown}
          onBlur={handleBlur}
          disabled={isSaving}
          min={min}
          max={max}
          placeholder={placeholder}
          className={cn(
            'h-8 w-20 text-sm',
            hasError && 'border-red-500 focus-visible:ring-red-500',
            className
          )}
        />
        {isSaving && (
          <div className="absolute inset-0 flex items-center justify-center bg-background/50">
            <div className="h-3 w-3 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          </div>
        )}
      </div>
    )
  }

  return (
    <button
      onClick={handleClick}
      disabled={disabled}
      className={cn(
        'h-8 min-w-[3rem] rounded px-2 text-left text-sm hover:bg-muted',
        'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
        disabled && 'cursor-not-allowed opacity-50',
        className
      )}
      title="Click to edit"
    >
      <span className="font-medium">{value ?? placeholder}</span>
    </button>
  )
}
