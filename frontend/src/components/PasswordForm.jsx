import { useState } from 'react'

import { Button } from './ui/Button'
import { TextField } from './ui/TextField'

export function PasswordForm({ onSubmit, loading, error }) {
  const [password, setPassword] = useState('')

  const handleSubmit = (event) => {
    event.preventDefault()
    if (password.trim()) onSubmit(password.trim())
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <TextField
        label="Senha do app"
        type="password"
        autoComplete="current-password"
        value={password}
        onChange={(event) => setPassword(event.target.value)}
        error={error}
        autoFocus
      />
      <Button type="submit" variant="accent" fullWidth loading={loading} disabled={!password.trim()}>
        Entrar
      </Button>
    </form>
  )
}
