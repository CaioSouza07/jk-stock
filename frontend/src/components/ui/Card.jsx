import { cn } from '../../utils/cn'

export function Card({ as: Component = 'section', padded = true, className, children, ...props }) {
  return (
    <Component
      className={cn('rounded-2xl border border-line bg-white shadow-sm', padded && 'p-4', className)}
      {...props}
    >
      {children}
    </Component>
  )
}
