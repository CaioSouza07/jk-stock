import { API_URL, apiRequest } from './client'

/**
 * Also used to validate the app password: throws ApiError 401 when wrong.
 * Default (long) timeout: a sleeping server can take ~50s to wake up.
 */
export function getAuthStatus(password) {
  return apiRequest('/auth/status', { password })
}

/**
 * Leaves the app for the Olist login. The backend callback brings the user back
 * to this page with ?olist=connected or ?olist_error=<message>.
 */
export function redirectToOlistLogin(password) {
  const returnTo = `${window.location.origin}${window.location.pathname}`
  const params = new URLSearchParams({ password, return_to: returnTo })
  window.location.assign(`${API_URL}/auth/login?${params}`)
}

/** Reads (and removes from the URL) the result of the Olist login callback. */
export function consumeOlistLoginResult() {
  const url = new URL(window.location.href)
  const connected = url.searchParams.get('olist') === 'connected'
  const error = url.searchParams.get('olist_error')
  if (!connected && !error) return null

  url.searchParams.delete('olist')
  url.searchParams.delete('olist_error')
  window.history.replaceState(null, '', url)
  return { connected, error }
}
