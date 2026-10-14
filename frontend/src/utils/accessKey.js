const ACCESS_KEY_RE = /(?<!\d)\d{44}(?!\d)/

/** Finds the 44-digit key in a scanned/typed text (barcode, QR URL, digits with spaces). */
export function extractAccessKey(text) {
  const match = (text ?? '').replace(/\s+/g, '').match(ACCESS_KEY_RE)
  return match ? match[0] : null
}

export function countDigits(text) {
  return (text ?? '').replace(/\D/g, '').length
}

export function formatAccessKey(key) {
  return key.replace(/(\d{4})(?=\d)/g, '$1 ')
}
