'use client'

/**
 * Category Title & Description Section
 *
 * Features:
 * - Simple title input
 * - Rich text editor for description (Tiptap)
 * - Toolbar: Heading, Bold, Italic, Underline, Alignment, Link
 * - Clean Shopify-like UI
 */

import { useEffect } from 'react'
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import TextAlign from '@tiptap/extension-text-align'
import Underline from '@tiptap/extension-underline'
import Link from '@tiptap/extension-link'
import { Card, CardContent } from '@/components/shadcn-ui/card'
import { Input } from '@/components/shadcn-ui/input'
import { Label } from '@/components/shadcn-ui/label'
import { Button } from '@/components/shadcn-ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/shadcn-ui/select'
import {
  Bold,
  Italic,
  Underline as UnderlineIcon,
  AlignLeft,
  AlignCenter,
  AlignRight,
  Link as LinkIcon,
  Code,
} from 'lucide-react'
import type { CategoryTitleDescriptionProps } from './types'

export function CategoryTitleDescriptionSection({
  title,
  description,
  onTitleChange,
  onDescriptionChange,
  errors,
}: CategoryTitleDescriptionProps) {

  // Initialize Tiptap editor
  const editor = useEditor({
    immediatelyRender: false, // Fix SSR hydration mismatch
    extensions: [
      StarterKit.configure({
        heading: {
          levels: [1, 2, 3],
        },
      }),
      TextAlign.configure({
        types: ['heading', 'paragraph'],
        alignments: ['left', 'center', 'right'],
      }),
      Underline,
      Link.configure({
        openOnClick: false,
        HTMLAttributes: {
          class: 'text-blue-600 underline',
        },
      }),
    ],
    content: description || '',
    onUpdate: ({ editor }) => {
      // Update parent state when editor content changes
      const html = editor.getHTML()
      onDescriptionChange(html)
    },
    editorProps: {
      attributes: {
        class: 'prose prose-sm max-w-none focus:outline-none min-h-[200px] p-4',
      },
    },
  })

  // Update editor when description changes externally
  useEffect(() => {
    if (editor && description !== editor.getHTML()) {
      editor.commands.setContent(description || '')
    }
  }, [description, editor])

  if (!editor) {
    return null
  }

  const setLink = () => {
    const previousUrl = editor.getAttributes('link').href
    const url = window.prompt('URL', previousUrl)

    if (url === null) {
      return
    }

    if (url === '') {
      editor.chain().focus().extendMarkRange('link').unsetLink().run()
      return
    }

    editor.chain().focus().extendMarkRange('link').setLink({ href: url }).run()
  }

  return (
    <Card>
      <CardContent className="pt-6 space-y-4">
        {/* Title Input */}
        <div className="space-y-2">
          <Label htmlFor="category-title">Title</Label>
          <Input
            id="category-title"
            value={title}
            onChange={(e) => onTitleChange(e.target.value)}
            placeholder="e.g. Home page"
            className={errors?.title ? 'border-red-500' : ''}
          />
          {errors?.title && (
            <p className="text-sm text-red-500">{errors.title}</p>
          )}
        </div>

        {/* Description Rich Text Editor */}
        <div className="space-y-2">
          <Label>Description</Label>

          {/* Toolbar */}
          <div className="border rounded-t-md bg-muted/30 p-2 flex items-center gap-1 flex-wrap">
            {/* Heading Dropdown */}
            <Select
              value={
                editor.isActive('heading', { level: 1 }) ? 'h1' :
                editor.isActive('heading', { level: 2 }) ? 'h2' :
                editor.isActive('heading', { level: 3 }) ? 'h3' :
                'paragraph'
              }
              onValueChange={(value) => {
                if (value === 'paragraph') {
                  editor.chain().focus().setParagraph().run()
                } else if (value === 'h1') {
                  editor.chain().focus().setHeading({ level: 1 }).run()
                } else if (value === 'h2') {
                  editor.chain().focus().setHeading({ level: 2 }).run()
                } else if (value === 'h3') {
                  editor.chain().focus().setHeading({ level: 3 }).run()
                }
              }}
            >
              <SelectTrigger className="w-[130px] h-8 bg-background">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="paragraph">Paragraph</SelectItem>
                <SelectItem value="h1">Heading 1</SelectItem>
                <SelectItem value="h2">Heading 2</SelectItem>
                <SelectItem value="h3">Heading 3</SelectItem>
              </SelectContent>
            </Select>

            <div className="h-6 w-px bg-border mx-1" />

            {/* Bold */}
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className={`h-8 w-8 ${editor.isActive('bold') ? 'bg-muted' : ''}`}
              onClick={() => editor.chain().focus().toggleBold().run()}
            >
              <Bold className="h-4 w-4" />
            </Button>

            {/* Italic */}
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className={`h-8 w-8 ${editor.isActive('italic') ? 'bg-muted' : ''}`}
              onClick={() => editor.chain().focus().toggleItalic().run()}
            >
              <Italic className="h-4 w-4" />
            </Button>

            {/* Underline */}
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className={`h-8 w-8 ${editor.isActive('underline') ? 'bg-muted' : ''}`}
              onClick={() => editor.chain().focus().toggleUnderline().run()}
            >
              <UnderlineIcon className="h-4 w-4" />
            </Button>

            <div className="h-6 w-px bg-border mx-1" />

            {/* Align Left */}
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className={`h-8 w-8 ${editor.isActive({ textAlign: 'left' }) ? 'bg-muted' : ''}`}
              onClick={() => editor.chain().focus().setTextAlign('left').run()}
            >
              <AlignLeft className="h-4 w-4" />
            </Button>

            {/* Align Center */}
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className={`h-8 w-8 ${editor.isActive({ textAlign: 'center' }) ? 'bg-muted' : ''}`}
              onClick={() => editor.chain().focus().setTextAlign('center').run()}
            >
              <AlignCenter className="h-4 w-4" />
            </Button>

            {/* Align Right */}
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className={`h-8 w-8 ${editor.isActive({ textAlign: 'right' }) ? 'bg-muted' : ''}`}
              onClick={() => editor.chain().focus().setTextAlign('right').run()}
            >
              <AlignRight className="h-4 w-4" />
            </Button>

            <div className="h-6 w-px bg-border mx-1" />

            {/* Link */}
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className={`h-8 w-8 ${editor.isActive('link') ? 'bg-muted' : ''}`}
              onClick={setLink}
            >
              <LinkIcon className="h-4 w-4" />
            </Button>

            {/* Code View */}
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className={`h-8 w-8 ${editor.isActive('code') ? 'bg-muted' : ''}`}
              onClick={() => editor.chain().focus().toggleCode().run()}
            >
              <Code className="h-4 w-4" />
            </Button>
          </div>

          {/* Editor Area */}
          <div className="border border-t-0 rounded-b-md min-h-[200px] bg-background">
            <EditorContent editor={editor} />
          </div>

          {errors?.description && (
            <p className="text-sm text-red-500">{errors.description}</p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
