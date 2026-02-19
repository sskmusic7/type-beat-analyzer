/**
 * API URL configuration for remote/local/production access
 * Priority: Environment variable > Production URL > Local development
 */
export function getApiBaseUrl(): string {
  // Production: use environment variable or default Cloud Run URL
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL
  }
  
  // Production fallback
  if (process.env.NODE_ENV === 'production') {
    return 'https://type-beat-backend-x2x4tp5wra-uc.a.run.app'
  }
  
  if (typeof window !== 'undefined') {
    // Browser: use same host as frontend, backend on port 8000 (local dev)
    return `${window.location.protocol}//${window.location.hostname}:8000`
  }
  
  // SSR/build: default to localhost
  return 'http://localhost:8000'
}
