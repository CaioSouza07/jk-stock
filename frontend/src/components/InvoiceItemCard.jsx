import { formatCurrency, formatQuantity } from '../utils/format'
import { ProductImage } from './ProductImage'
import { Card } from './ui/Card'

export function InvoiceItemCard({ item }) {
  return (
    <Card as="li" className="flex gap-3 p-3">
      <ProductImage src={item.image_url} alt={item.description} className="size-20" />

      <div className="flex min-w-0 flex-1 flex-col">
        <p className="line-clamp-2 font-semibold leading-snug">{item.description}</p>
        {item.code && <p className="mt-0.5 text-xs text-muted">SKU {item.code}</p>}

        <div className="mt-auto flex items-end justify-between gap-2 pt-2">
          <p className="text-sm text-muted">
            <span className="inline-block rounded-md bg-accent px-2 py-0.5 font-bold text-on-accent">
              {formatQuantity(item.quantity)} {item.unit}
            </span>
            <span className="ml-2">× {formatCurrency(item.unit_price)}</span>
          </p>
          <p className="font-bold text-primary">{formatCurrency(item.total_price)}</p>
        </div>
      </div>
    </Card>
  )
}
