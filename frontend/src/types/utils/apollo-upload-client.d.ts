declare module 'apollo-upload-client/UploadHttpLink.mjs' {
  import { ApolloLink } from '@apollo/client'

  export interface UploadHttpLinkOptions {
    uri?: string | ((operation: any) => string)
    credentials?: string
    headers?: Record<string, string>
    fetch?: typeof fetch
    fetchOptions?: RequestInit
    includeExtensions?: boolean
    useGETForQueries?: boolean
    isExtractableFile?: (value: any) => boolean
    FormData?: typeof FormData
    formDataAppendFile?: (formData: FormData, fieldName: string, file: any) => void
    includeUnusedVariables?: boolean
    print?: any
    [key: string]: any
  }

  export default class UploadHttpLink extends ApolloLink {
    constructor(options?: UploadHttpLinkOptions)
  }
}
