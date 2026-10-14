const currency = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })
const quantity = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 3 })

export const formatCurrency = (value) => currency.format(value ?? 0)

export const formatQuantity = (value) => quantity.format(value ?? 0)

/** "2024-01-15..." -> "15/01/2024" without timezone shifts. */
export function formatDate(isoDate) {
  if (!isoDate) return '—'
  const [year, month, day] = isoDate.slice(0, 10).split('-')
  return year && month && day ? `${day}/${month}/${year}` : isoDate
}
