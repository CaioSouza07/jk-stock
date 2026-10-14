import { cn } from '../../utils/cn'

const SIZES = {
  sm: 'size-4 border-2',
  md: 'size-6 border-2',
  lg: 'size-10 border-4',
}

export function Spinner({ size = 'md', className }) {
  return (
    <span
      role="status"
      aria-label="Carregando"
      className={cn(
        'inline-block animate-spin rounded-full border-current border-r-transparent',
        SIZES[size],
        className,
      )}
    />
  )
}
