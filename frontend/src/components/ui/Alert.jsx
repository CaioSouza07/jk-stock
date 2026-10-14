import { cn } from '../../utils/cn'

const VARIANTS = {
  error: 'border-danger/30 bg-danger-soft text-danger',
  warning: 'border-accent/40 bg-accent/10 text-on-accent',
  info: 'border-secondary bg-background text-primary',
}

export function Alert({ variant = 'error', title, className, children }) {
  return (
    <div
      role={variant === 'error' ? 'alert' : 'status'}
      className={cn('rounded-xl border px-4 py-3 text-sm', VARIANTS[variant], className)}
    >
      {title && <p className="font-semibold">{title}</p>}
      <div>{children}</div>
    </div>
  )
}
