import { useEffect } from 'react'

import { InvoiceItemCard } from '../components/InvoiceItemCard'
import { InvoiceSummary } from '../components/InvoiceSummary'
import { Button } from '../components/ui/Button'

function SectionTitle({ children }) {
  return (
    <h2 className="text-sm font-bold uppercase tracking-wide text-primary-light">{children}</h2>
  )
}

/** Products first (what the user is checking); invoice details at the end. */
export function InvoicePage({ invoice, onNewScan }) {
  useEffect(() => {
    window.scrollTo({ top: 0 })
  }, [invoice])

  return (
    <div className="flex flex-col gap-4 pb-24">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-primary-light">
          NF nº {invoice.number} · Série {invoice.series}
        </p>
        <h1 className="text-xl font-extrabold text-primary">
          Produtos ({invoice.items.length})
        </h1>
      </div>

      {invoice.items.length === 0 ? (
        <p className="text-sm text-muted">Esta nota não tem itens.</p>
      ) : (
        <ul className="flex flex-col gap-4">
          {invoice.items.map((item, index) => (
            <InvoiceItemCard key={`${item.product_id}-${index}`} item={item} />
          ))}
        </ul>
      )}

      <SectionTitle>Dados da nota</SectionTitle>
      <InvoiceSummary invoice={invoice} />

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
