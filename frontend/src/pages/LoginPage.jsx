import { useState } from 'react'

import { getAuthStatus } from '../api/auth'
import { PasswordForm } from '../components/PasswordForm'
import { Alert } from '../components/ui/Alert'
import { Card } from '../components/ui/Card'

export function LoginPage({ notice, onLogin }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (password) => {
    setLoading(true)
    setError(null)
    try {
      await getAuthStatus(password)
      onLogin(password)
    } catch (loginError) {
      setError(loginError.status === 401 ? 'Senha incorreta.' : loginError.message)
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col gap-4 pt-6">
      {notice && <Alert variant="warning">{notice}</Alert>}
      <Card className="p-6">
        <h1 className="text-xl font-extrabold text-primary">Entrar</h1>
        <p className="mb-5 mt-1 text-sm text-muted">
          Digite a senha do app para consultar as notas fiscais.
        </p>
        <PasswordForm onSubmit={handleSubmit} loading={loading} error={error} />
      </Card>
    </div>
  )
}
