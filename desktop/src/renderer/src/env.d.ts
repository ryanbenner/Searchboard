/// <reference types="vite/client" />
import type { SearchboardApi } from '../../shared/types'

declare global {
  interface Window {
    searchboard: SearchboardApi
  }
}
