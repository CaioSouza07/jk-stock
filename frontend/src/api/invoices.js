import { apiRequest } from './client'

export function lookupInvoice(barcode, password) {
  return apiRequest('/api/invoices/lookup', { method: 'POST', password, body: { barcode } })
}
