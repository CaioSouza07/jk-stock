import { useId } from 'react'

import { cn } from '../../utils/cn'

export function TextField({ label, hint, error, className, ...inputProps }) {
  const id = useId()
  const hintId = `${id}-hint`

  return (
    <div className={cn('flex flex-col gap-1.5', className)}>
      <label htmlFor={id} className="text-sm font-semibold text-ink">
        {label}
      </label>
      <input
        id={id}
        aria-invalid={Boolean(error)}
        aria-describedby={hint || error ? hintId : undefined}
        className={cn(
          'h-12 rounded-xl border-2 bg-white px-4 text-base text-ink outline-none transition-colors',
          'placeholder:text-muted/70 focus:border-primary-light',
          error ? 'border-danger' : 'border-line',
        )}
        {...inputProps}
      />
      {(error || hint) && (
        <p id={hintId} className={cn('text-xs', error ? 'text-danger' : 'text-muted')}>
          {error || hint}
        </p>
      )}
    </div>
  )
}
