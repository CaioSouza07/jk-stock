import { apiRequest } from './client'

/** Also used to validate the app password: throws ApiError 401 when wrong. */
export function getAuthStatus(password) {
  return apiRequest('/auth/status', { password, timeoutMs: 15_000 })
}
