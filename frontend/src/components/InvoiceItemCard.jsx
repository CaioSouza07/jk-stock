import { formatCurrency, formatQuantity } from '../utils/format'
import { ProductGallery } from './ProductGallery'
import { Card } from './ui/Card'

export function InvoiceItemCard({ item }) {
  return (
    <Card as="li" padded={false} className="overflow-hidden">
      <ProductGallery images={item.images} alt={item.description} />

      <div className="flex flex-col gap-3 border-t border-line p-4">
        <div>
          <p className="text-lg font-bold leading-snug break-words">{item.description}</p>
          {item.code && <p className="mt-1 text-xs text-muted">SKU {item.code}</p>}
        </div>

        <div className="flex items-end justify-between gap-3">
          <div>
            <span className="block text-xs text-muted">Quantidade</span>
            <span className="mt-1 inline-block rounded-lg bg-accent px-3 py-1 text-lg font-extrabold text-on-accent">
              {formatQuantity(item.quantity)} {item.unit}
            </span>
          </div>
          <div className="text-right">
            <span className="block text-xs text-muted">
              {formatCurrency(item.unit_price)} {item.unit ? `/ ${item.unit}` : 'cada'}
            </span>
            <span className="text-lg font-extrabold text-primary">
              {formatCurrency(item.total_price)}
            </span>
          </div>
        </div>
      </div>
    </Card>
  )
}
