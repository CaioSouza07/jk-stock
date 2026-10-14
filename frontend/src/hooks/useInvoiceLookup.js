import { useCallback, useState } from 'react'

import { lookupInvoice } from '../api/invoices'

const IDLE = { status: 'idle', invoice: null, error: null, barcode: null }

/**
 * status: idle -> loading -> success | error.
 * A 401 means the stored password is no longer valid: onUnauthorized is called instead.
 * Olist disconnected (session expired): onOlistDisconnected is called instead.
 */
export function useInvoiceLookup(password, onUnauthorized, onOlistDisconnected) {
  const [state, setState] = useState(IDLE)

  const lookup = useCallback(
    async (barcode) => {
      setState({ ...IDLE, status: 'loading', barcode })
      try {
        const invoice = await lookupInvoice(barcode, password)
        setState({ ...IDLE, status: 'success', invoice, barcode })
      } catch (error) {
        if (error.status === 401) {
          setState(IDLE)
          onUnauthorized()
          return
        }
        if (error.code === 'olist_not_connected') {
          setState(IDLE)
          onOlistDisconnected()
          return
        }
        setState({ ...IDLE, status: 'error', error: error.message, barcode })
      }
    },
    [password, onUnauthorized, onOlistDisconnected],
  )

  const reset = useCallback(() => setState(IDLE), [])

  return { ...state, lookup, reset }
}
