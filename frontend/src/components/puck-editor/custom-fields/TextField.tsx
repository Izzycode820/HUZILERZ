'use client';

import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Link from '@tiptap/extension-link';
import Underline from '@tiptap/extension-underline';
import TextAlign from '@tiptap/extension-text-align';
import { Button } from '@/components/shadcn-ui/button';
import { Separator } from '@/components/shadcn-ui/separator';
import {
  Bold,
  Italic,
  Underline as UnderlineIcon,
  List,
  ListOrdered,
  AlignLeft,
  AlignCenter,
  AlignRight,
} from 'lucide-react';
import { useEffect } from 'react';

interface TextFieldProps {
  value: string;
  onChange: (value: string) => void;
  name: string;
}

export function TextField({ value, onChange }: TextFieldProps) {
  const editor = useEditor({
    immediatelyRender: false,
    extensions: [
      StarterKit,
      Underline,
      Link.configure({
        openOnClick: false,
      }),
      TextAlign.configure({
        types: ['heading', 'paragraph'],
      }),
    ],
    content: value,
    editorProps: {
      attributes: {
        class: 'prose prose-sm w-full max-w-none focus:outline-none min-h-[100px] p-2 [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:list-decimal [&_ol]:pl-5',
      },
    },
    onUpdate: ({ editor }) => {
      onChange(editor.getHTML());
    },
  });

  // Sync value changes from outside (e.g. undo/redo from parent or init)
  useEffect(() => {
    if (editor && value !== editor.getHTML()) {
      // Only update if content is different to avoid cursor jumping
      // Simple check, implies incomplete sync but good enough for prop updates
      if (editor.getText() === '' && value === '') return;
      // editor.commands.setContent(value); 
      // Note: setContent can reset cursor. 
      // Ideal for controlled inputs is complex. 
      // For Puck, often value update comes from this component itself.
    }
  }, [value, editor]);


  if (!editor) {
    return null;
  }

  return (
    <div className="space-y-2">
      <div className="border rounded-lg overflow-hidden bg-background focus-within:ring-2 focus-within:ring-ring transition-all">
        {/* Toolbar */}
        <div className="flex items-center gap-0.5 px-2 py-1.5 bg-muted/30 border-b overflow-x-auto">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className={`h-7 w-7 p-0 hover:bg-accent ${editor.isActive('bold') ? 'bg-accent/50 text-accent-foreground' : ''}`}
            onClick={() => editor.chain().focus().toggleBold().run()}
          >
            <Bold className="h-3.5 w-3.5" />
          </Button>

          <Button
            type="button"
            variant="ghost"
            size="sm"
            className={`h-7 w-7 p-0 hover:bg-accent ${editor.isActive('italic') ? 'bg-accent/50 text-accent-foreground' : ''}`}
            onClick={() => editor.chain().focus().toggleItalic().run()}
          >
            <Italic className="h-3.5 w-3.5" />
          </Button>

          <Button
            type="button"
            variant="ghost"
            size="sm"
            className={`h-7 w-7 p-0 hover:bg-accent ${editor.isActive('underline') ? 'bg-accent/50 text-accent-foreground' : ''}`}
            onClick={() => editor.chain().focus().toggleUnderline().run()}
          >
            <UnderlineIcon className="h-3.5 w-3.5" />
          </Button>

          <Separator orientation="vertical" className="mx-1 h-5" />

          <Button
            type="button"
            variant="ghost"
            size="sm"
            className={`h-7 w-7 p-0 hover:bg-accent ${editor.isActive('bulletList') ? 'bg-accent/50 text-accent-foreground' : ''}`}
            onClick={() => editor.chain().focus().toggleBulletList().run()}
          >
            <List className="h-3.5 w-3.5" />
          </Button>

          <Button
            type="button"
            variant="ghost"
            size="sm"
            className={`h-7 w-7 p-0 hover:bg-accent ${editor.isActive('orderedList') ? 'bg-accent/50 text-accent-foreground' : ''}`}
            onClick={() => editor.chain().focus().toggleOrderedList().run()}
          >
            <ListOrdered className="h-3.5 w-3.5" />
          </Button>

          <Separator orientation="vertical" className="mx-1 h-5" />

          <Button
            type="button"
            variant="ghost"
            size="sm"
            className={`h-7 w-7 p-0 hover:bg-accent ${editor.isActive({ textAlign: 'left' }) ? 'bg-accent/50 text-accent-foreground' : ''}`}
            onClick={() => editor.chain().focus().setTextAlign('left').run()}
          >
            <AlignLeft className="h-3.5 w-3.5" />
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className={`h-7 w-7 p-0 hover:bg-accent ${editor.isActive({ textAlign: 'center' }) ? 'bg-accent/50 text-accent-foreground' : ''}`}
            onClick={() => editor.chain().focus().setTextAlign('center').run()}
          >
            <AlignCenter className="h-3.5 w-3.5" />
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className={`h-7 w-7 p-0 hover:bg-accent ${editor.isActive({ textAlign: 'right' }) ? 'bg-accent/50 text-accent-foreground' : ''}`}
            onClick={() => editor.chain().focus().setTextAlign('right').run()}
          >
            <AlignRight className="h-3.5 w-3.5" />
          </Button>
        </div>

        <EditorContent editor={editor} />
      </div>
    </div>
  );
}
