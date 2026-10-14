import { formatAccessKey } from '../utils/accessKey'
import { formatCurrency, formatDate } from '../utils/format'
import { Card } from './ui/Card'

function Field({ label, children }) {
  return (
    <div>
      <dt className="text-xs text-muted">{label}</dt>
      <dd className="font-semibold">{children}</dd>
    </div>
  )
}

export function InvoiceSummary({ invoice }) {
  return (
    <Card className="border-l-4 border-l-accent">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-primary-light">
            Nota fiscal
          </p>
          <h1 className="text-2xl font-extrabold text-primary">
            Nº {invoice.number}
            <span className="ml-2 text-base font-semibold text-muted">Série {invoice.series}</span>
          </h1>
        </div>
        <p className="text-right">
          <span className="block text-xs text-muted">Total</span>
          <span className="text-xl font-extrabold text-primary">{formatCurrency(invoice.total)}</span>
        </p>
      </div>

      <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
        <Field label="Emissão">{formatDate(invoice.issued_at)}</Field>
        <Field label="Itens">{invoice.items.length}</Field>
        {invoice.customer_name && (
          <div className="col-span-2">
            <Field label="Cliente">{invoice.customer_name}</Field>
          </div>
        )}
      </dl>

      <p className="mt-4 break-all font-mono text-xs text-muted">
        {formatAccessKey(invoice.access_key)}
      </p>
    </Card>
  )
}
