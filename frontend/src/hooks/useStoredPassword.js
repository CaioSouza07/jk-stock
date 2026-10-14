import { useCallback, useState } from 'react'

const STORAGE_KEY = 'jkstock.appPassword'

/** App password persisted on the device so the user types it only once. */
export function useStoredPassword() {
  const [password, setPassword] = useState(() => localStorage.getItem(STORAGE_KEY))

  const save = useCallback((value) => {
    localStorage.setItem(STORAGE_KEY, value)
    setPassword(value)
  }, [])

  const clear = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY)
    setPassword(null)
  }, [])

  return { password, save, clear }
}
