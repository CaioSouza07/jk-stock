import { useRef } from 'react'

import { useBarcodeScanner } from '../hooks/useBarcodeScanner'
import { cn } from '../utils/cn'
import { Alert } from './ui/Alert'
import { Spinner } from './ui/Spinner'

function ControlButton({ active, label, onClick, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={label}
      aria-pressed={active}
      className={cn(
        'flex size-11 items-center justify-center rounded-full text-sm font-bold backdrop-blur transition-colors',
        active ? 'bg-accent text-on-accent' : 'bg-ink/60 text-white',
      )}
    >
      {children}
    </button>
  )
}

function TorchIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className="size-5" aria-hidden="true">
      <path d="M13 2 4 14h7l-1 8 9-12h-7l1-8Z" />
    </svg>
  )
}

/** Guide band: the DANFE barcode is wide and thin */
function Viewfinder() {
  return (
    <div className="pointer-events-none absolute inset-x-[6%] top-1/2 h-1/3 -translate-y-1/2 rounded-lg border-2 border-accent shadow-[0_0_0_9999px_rgb(16_35_61/35%)]">
      <div className="absolute inset-x-2 top-1/2 h-0.5 animate-pulse bg-accent" />
    </div>
  )
}

/** Opens the rear camera and calls onScan(accessKey) once a 44-digit key is read. */
export function BarcodeScanner({ onScan }) {
  const videoRef = useRef(null)
  const { error, ready, torch, zoom } = useBarcodeScanner({ videoRef, onDetect: onScan })

  if (error) return <Alert variant="warning">{error}</Alert>

  return (
    <div className="relative aspect-[4/3] w-full overflow-hidden rounded-2xl border-4 border-primary bg-ink">
      {/* playsInline + muted are required for autoplay on iPhone */}
      <video ref={videoRef} muted playsInline className="size-full object-cover" />

      {ready ? (
        <Viewfinder />
      ) : (
        <div className="absolute inset-0 flex items-center justify-center text-white">
          <Spinner size="lg" />
        </div>
      )}

      {ready && (torch.supported || zoom.supported) && (
        <div className="absolute right-3 top-3 flex flex-col gap-2">
          {torch.supported && (
            <ControlButton active={torch.on} label="Lanterna" onClick={torch.toggle}>
              <TorchIcon />
            </ControlButton>
          )}
          {zoom.supported && (
            <ControlButton active={zoom.on} label="Zoom 2x" onClick={zoom.toggle}>
              2x
            </ControlButton>
          )}
        </div>
      )}

      <p className="pointer-events-none absolute inset-x-0 bottom-0 bg-ink/60 px-3 py-2 text-center text-xs text-white">
        Deixe o código de barras na horizontal, dentro da faixa laranja
      </p>
    </div>
  )
}
