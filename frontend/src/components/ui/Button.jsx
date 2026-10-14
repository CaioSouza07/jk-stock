import { cn } from '../../utils/cn'
import { Spinner } from './Spinner'

const VARIANTS = {
  primary: 'bg-primary text-white hover:bg-primary-light',
  accent: 'bg-accent text-on-accent hover:bg-accent-hover',
  outline: 'border-2 border-primary bg-white text-primary hover:bg-background',
  ghost: 'text-white hover:bg-white/15',
}

const SIZES = {
  sm: 'h-9 px-3 text-sm',
  md: 'h-12 px-5 text-base',
}

export function Button({
  variant = 'primary',
  size = 'md',
  fullWidth = false,
  loading = false,
  disabled,
  className,
  children,
  ...props
}) {
  return (
    <button
      type="button"
      disabled={disabled || loading}
      className={cn(
        'inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition-colors',
        'focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-accent',
        'disabled:cursor-not-allowed disabled:opacity-50',
        VARIANTS[variant],
        SIZES[size],
        fullWidth && 'w-full',
        className,
      )}
      {...props}
    >
      {loading && <Spinner size="sm" />}
      {children}
    </button>
  )
}
