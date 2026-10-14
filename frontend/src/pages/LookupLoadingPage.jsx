import { Spinner } from '../components/ui/Spinner'
import { formatAccessKey } from '../utils/accessKey'

export function LookupLoadingPage({ accessKey }) {
  return (
    <div className="flex flex-col items-center gap-4 pt-16 text-center">
      <Spinner size="lg" className="text-primary" />
      <div>
        <p className="font-semibold text-primary">Buscando nota no Olist…</p>
        <p className="mt-2 break-all font-mono text-xs text-muted">{formatAccessKey(accessKey)}</p>
      </div>
    </div>
  )
}
