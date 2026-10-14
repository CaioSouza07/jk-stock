import { useState } from 'react'

import { cn } from '../utils/cn'

function Placeholder() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="size-8" aria-hidden="true">
      <path d="M21 7.5 12 3 3 7.5m18 0-9 4.5m9-4.5v9L12 21m0-9L3 7.5m9 4.5v9M3 7.5v9L12 21" />
    </svg>
  )
}

export function ProductImage({ src, alt, className }) {
  const [failed, setFailed] = useState(false)

  return (
    <div
      className={cn(
        'flex shrink-0 items-center justify-center overflow-hidden rounded-xl bg-background text-secondary',
        className,
      )}
    >
      {src && !failed ? (
        <img
          src={src}
          alt={alt}
          loading="lazy"
          className="size-full object-cover"
          onError={() => setFailed(true)}
        />
      ) : (
        <Placeholder />
      )}
    </div>
  )
}
