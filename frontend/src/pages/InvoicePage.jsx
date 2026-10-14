import { useEffect } from 'react'

import { InvoiceItemCard } from '../components/InvoiceItemCard'
import { InvoiceSummary } from '../components/InvoiceSummary'
import { Button } from '../components/ui/Button'

export function InvoicePage({ invoice, onNewScan }) {
  useEffect(() => {
    window.scrollTo({ top: 0 })
  }, [invoice])

  return (
    <div className="flex flex-col gap-4 pb-24">
      <InvoiceSummary invoice={invoice} />

      <h2 className="text-sm font-bold uppercase tracking-wide text-primary-light">
        Produtos ({invoice.items.length})
      </h2>

      {invoice.items.length === 0 ? (
        <p className="text-sm text-muted">Esta nota não tem itens.</p>
      ) : (
        <ul className="flex flex-col gap-3">
          {invoice.items.map((item, index) => (
            <InvoiceItemCard key={`${item.product_id}-${index}`} item={item} />
          ))}
        </ul>
      )}

      <div className="fixed inset-x-0 bottom-0 border-t border-line bg-white/95 p-4 backdrop-blur">
        <div className="mx-auto max-w-xl">
          <Button variant="accent" fullWidth onClick={onNewScan}>
            Ler outra nota
          </Button>
        </div>
      </div>
    </div>
  )
}
