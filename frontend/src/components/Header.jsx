import { Button } from './ui/Button'

export function Header({ onLogout }) {
  return (
    <header className="sticky top-0 z-10 bg-primary text-white shadow-md">
      <div className="mx-auto flex h-14 max-w-xl items-center justify-between px-4">
        <div className="flex items-baseline gap-2">
          <span className="text-lg font-extrabold tracking-wide">JKSTOCK</span>
          <span className="text-xs text-secondary">Leitor DANFE</span>
        </div>
        {onLogout && (
          <Button variant="ghost" size="sm" onClick={onLogout}>
            Sair
          </Button>
        )}
      </div>
      <div className="h-1 bg-accent" />
    </header>
  )
}
