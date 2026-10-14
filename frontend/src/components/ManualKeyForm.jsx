import { useState } from 'react'

import { countDigits, extractAccessKey } from '../utils/accessKey'
import { Button } from './ui/Button'
import { TextField } from './ui/TextField'

export function ManualKeyForm({ onSubmit }) {
  const [value, setValue] = useState('')
  const key = extractAccessKey(value)

  const handleSubmit = (event) => {
    event.preventDefault()
    if (key) onSubmit(key)
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      <TextField
        label="Chave de acesso"
        inputMode="numeric"
        autoComplete="off"
        placeholder="44 dígitos abaixo do código de barras"
        value={value}
        onChange={(event) => setValue(event.target.value)}
        hint={`${countDigits(value)}/44 dígitos`}
      />
      <Button type="submit" variant="outline" fullWidth disabled={!key}>
        Buscar nota
      </Button>
    </form>
  )
}
