import { cn } from '../../utils/cn'

export function Card({ as: Component = 'section', className, children, ...props }) {
  return (
    <Component
      className={cn('rounded-2xl border border-line bg-white p-4 shadow-sm', className)}
      {...props}
    >
      {children}
    </Component>
  )
}
