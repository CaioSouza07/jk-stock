import { Spinner } from '../components/ui/Spinner'

export function OlistRedirectPage() {
  return (
    <div className="flex flex-col items-center gap-4 pt-16 text-center">
      <Spinner size="lg" className="text-primary" />
      <div>
        <p className="font-semibold text-primary">Conectando ao Olist…</p>
        <p className="mt-2 text-sm text-muted">
          A sessão do Olist expirou. Você será levado para a tela de login do Olist.
        </p>
      </div>
    </div>
  )
}
