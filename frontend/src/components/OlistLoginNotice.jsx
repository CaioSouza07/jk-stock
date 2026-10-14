import { Alert } from './ui/Alert'
import { Button } from './ui/Button'

/** Result of the Olist login, shown when the callback brings the user back to the app. */
export function OlistLoginNotice({ result, onConnect }) {
  if (result.connected) return <Alert variant="info">Olist conectado com sucesso.</Alert>

  return (
    <Alert variant="error" title="Não foi possível conectar ao Olist">
      <p>{result.error}</p>
      <Button variant="primary" size="sm" className="mt-3" onClick={onConnect}>
        Conectar ao Olist
      </Button>
    </Alert>
  )
}
