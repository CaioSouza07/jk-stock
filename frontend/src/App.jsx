import { useCallback, useState } from 'react'

import { Header } from './components/Header'
import { useInvoiceLookup } from './hooks/useInvoiceLookup'
import { useStoredPassword } from './hooks/useStoredPassword'
import { InvoicePage } from './pages/InvoicePage'
import { LoginPage } from './pages/LoginPage'
import { LookupErrorPage } from './pages/LookupErrorPage'
import { LookupLoadingPage } from './pages/LookupLoadingPage'
import { ScanPage } from './pages/ScanPage'

export default function App() {
  const { password, save: savePassword, clear: clearPassword } = useStoredPassword()
  const [loginNotice, setLoginNotice] = useState(null)

  const handleUnauthorized = useCallback(() => {
    setLoginNotice('A senha do app foi alterada. Entre novamente.')
    clearPassword()
  }, [clearPassword])

  const invoiceLookup = useInvoiceLookup(password, handleUnauthorized)

  const handleLogin = (newPassword) => {
    setLoginNotice(null)
    savePassword(newPassword)
  }

  const handleLogout = () => {
    invoiceLookup.reset()
    clearPassword()
  }

  const renderPage = () => {
    if (!password) return <LoginPage notice={loginNotice} onLogin={handleLogin} />

    switch (invoiceLookup.status) {
      case 'loading':
        return <LookupLoadingPage accessKey={invoiceLookup.barcode} />
      case 'error':
        return (
          <LookupErrorPage
            message={invoiceLookup.error}
            onRetry={() => invoiceLookup.lookup(invoiceLookup.barcode)}
            onNewScan={invoiceLookup.reset}
          />
        )
      case 'success':
        return <InvoicePage invoice={invoiceLookup.invoice} onNewScan={invoiceLookup.reset} />
      default:
        return <ScanPage onKey={invoiceLookup.lookup} />
    }
  }

  return (
    <div className="min-h-svh">
      <Header onLogout={password ? handleLogout : undefined} />
      <main className="mx-auto max-w-xl px-4 py-5">{renderPage()}</main>
    </div>
  )
}
