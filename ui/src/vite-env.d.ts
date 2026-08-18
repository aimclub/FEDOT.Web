/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Overrides the API base path; defaults to the same-origin `/api`. */
  readonly VITE_API_BASE?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
