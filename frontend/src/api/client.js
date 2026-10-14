const DEFAULT_TIMEOUT_MS = 60_000

// Backend address (VITE_API_URL at build time). Empty in dev: Vite proxies the routes.
export const API_URL = (import.meta.env.VITE_API_URL ?? '').replace(/\/+$/, '')

export class ApiError extends Error {
  constructor(status, message, code = null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

/**
 * fetch wrapper for the backend. Throws ApiError with the backend's
 * Portuguese `detail` message and optional `code`; status 0 means network failure or timeout.
 */
export async function apiRequest(path, { method = 'GET', password, body, timeoutMs = DEFAULT_TIMEOUT_MS } = {}) {
  const headers = { Accept: 'application/json' }
  if (password) headers['X-App-Password'] = password
  if (body !== undefined) headers['Content-Type'] = 'application/json'

  let response
  try {
    response = await fetch(`${API_URL}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: AbortSignal.timeout(timeoutMs),
    })
  } catch (error) {
    if (error.name === 'TimeoutError') {
      throw new ApiError(0, 'O servidor demorou para responder. Tente novamente.')
    }
    throw new ApiError(0, 'Não foi possível conectar ao servidor. Verifique sua conexão.')
  }

  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new ApiError(
      response.status,
      data?.detail ?? `Erro inesperado (${response.status}).`,
      data?.code ?? null,
    )
  }
  return data
}
