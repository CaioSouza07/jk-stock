import { lazy, Suspense } from 'react'

import { ManualKeyForm } from '../components/ManualKeyForm'
import { Card } from '../components/ui/Card'
import { Spinner } from '../components/ui/Spinner'

// html5-qrcode is most of the bundle: load it only when this page opens
const BarcodeScanner = lazy(() =>
  import('../components/BarcodeScanner').then((module) => ({ default: module.BarcodeScanner })),
)

function ScannerFallback() {
  return (
    <div className="flex aspect-[4/3] w-full items-center justify-center rounded-2xl border-4 border-primary bg-ink text-white">
      <Spinner size="lg" />
    </div>
  )
}

function Divider({ children }) {
  return (
    <div className="flex items-center gap-3 text-xs font-semibold uppercase text-muted">
      <span className="h-px flex-1 bg-line" />
      {children}
      <span className="h-px flex-1 bg-line" />
    </div>
  )
}

export function ScanPage({ onKey }) {
  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-xl font-extrabold text-primary">Ler nota fiscal</h1>
        <p className="text-sm text-muted">Use a câmera ou digite a chave de acesso.</p>
      </div>

      <Suspense fallback={<ScannerFallback />}>
        <BarcodeScanner onScan={onKey} />
      </Suspense>

      <Divider>ou</Divider>

      <Card>
        <ManualKeyForm onSubmit={onKey} />
      </Card>
    </div>
  )
}
