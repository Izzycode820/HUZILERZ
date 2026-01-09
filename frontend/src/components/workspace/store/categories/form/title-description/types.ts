export interface CategoryTitleDescriptionProps {
  // Controlled values
  title: string
  description: string

  // Change handlers
  onTitleChange: (value: string) => void
  onDescriptionChange: (value: string) => void

  // Optional validation
  errors?: {
    title?: string
    description?: string
  }
}
