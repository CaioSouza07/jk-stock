const DEFAULT_TIMEOUT_MS = 60_000

export class ApiError extends Error {
  constructor(status, message) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

/**
 * fetch wrapper for the backend. Throws ApiError with the backend's
 * Portuguese `detail` message; status 0 means network failure or timeout.
 */
export async function apiRequest(path, { method = 'GET', password, body, timeoutMs = DEFAULT_TIMEOUT_MS } = {}) {
  const headers = { Accept: 'application/json' }
  if (password) headers['X-App-Password'] = password
  if (body !== undefined) headers['Content-Type'] = 'application/json'

  let response
  try {
    response = await fetch(path, {
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
    throw new ApiError(response.status, data?.detail ?? `Erro inesperado (${response.status}).`)
  }
  return data
}
