import { Alert } from '../components/ui/Alert'
import { Button } from '../components/ui/Button'

export function LookupErrorPage({ message, onRetry, onNewScan }) {
  return (
    <div className="flex flex-col gap-4 pt-6">
      <Alert variant="error" title="Não foi possível carregar a nota">
        {message}
      </Alert>
      <Button variant="primary" fullWidth onClick={onRetry}>
        Tentar novamente
      </Button>
      <Button variant="outline" fullWidth onClick={onNewScan}>
        Ler outra nota
      </Button>
    </div>
  )
}
