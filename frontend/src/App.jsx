import { useCallback, useEffect, useState } from 'react'

import { consumeOlistLoginResult, getAuthStatus, redirectToOlistLogin } from './api/auth'
import { Header } from './components/Header'
import { OlistLoginNotice } from './components/OlistLoginNotice'
import { useInvoiceLookup } from './hooks/useInvoiceLookup'
import { useStoredPassword } from './hooks/useStoredPassword'
import { InvoicePage } from './pages/InvoicePage'
import { LoginPage } from './pages/LoginPage'
import { LookupErrorPage } from './pages/LookupErrorPage'
import { LookupLoadingPage } from './pages/LookupLoadingPage'
import { OlistRedirectPage } from './pages/OlistRedirectPage'
import { ScanPage } from './pages/ScanPage'

// Read once per page load (outside React: StrictMode would run an initializer twice)
const initialOlistLogin = consumeOlistLoginResult()

export default function App() {
  const { password, save: savePassword, clear: clearPassword } = useStoredPassword()
  const [loginNotice, setLoginNotice] = useState(null)
  const [olistLogin, setOlistLogin] = useState(initialOlistLogin)
  const [redirecting, setRedirecting] = useState(false)

  const handleUnauthorized = useCallback(() => {
    setLoginNotice('A senha do app foi alterada. Entre novamente.')
    clearPassword()
  }, [clearPassword])

  const connectOlist = useCallback(() => {
    setRedirecting(true)
    redirectToOlistLogin(password)
  }, [password])

  const invoiceLookup = useInvoiceLookup(password, handleUnauthorized, connectOlist)

  // "Back" from the Olist login restores this page from the bfcache still redirecting
  useEffect(() => {
    const handlePageShow = (event) => {
      if (event.persisted) setRedirecting(false)
    }
    window.addEventListener('pageshow', handlePageShow)
    return () => window.removeEventListener('pageshow', handlePageShow)
  }, [])

  // Olist disconnected -> straight to its login. Not while showing a failed login,
  // otherwise a cancelled login would send the user back to Olist in a loop.
  const olistLoginFailed = Boolean(olistLogin?.error)
  useEffect(() => {
    if (!password || olistLoginFailed) return
    let cancelled = false
    getAuthStatus(password)
      .then((status) => {
        if (!cancelled && !status.connected) connectOlist()
      })
      .catch((error) => {
        if (!cancelled && error.status === 401) handleUnauthorized()
      })
    return () => {
      cancelled = true
    }
  }, [password, olistLoginFailed, connectOlist, handleUnauthorized])

  const handleLogin = (newPassword) => {
    setLoginNotice(null)
    setOlistLogin(null)
    savePassword(newPassword)
  }

  const handleLogout = () => {
    invoiceLookup.reset()
    setOlistLogin(null)
    clearPassword()
  }

  const handleScan = (barcode) => {
    if (olistLogin?.connected) setOlistLogin(null)
    invoiceLookup.lookup(barcode)
  }

  const renderPage = () => {
    if (!password) return <LoginPage notice={loginNotice} onLogin={handleLogin} />
    if (redirecting) return <OlistRedirectPage />

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
        return (
          <div className="flex flex-col gap-4">
            {olistLogin && <OlistLoginNotice result={olistLogin} onConnect={connectOlist} />}
            <ScanPage onKey={handleScan} />
          </div>
        )
    }
  }

  return (
    <div className="min-h-svh">
      <Header onLogout={password ? handleLogout : undefined} />
      <main className="mx-auto max-w-xl px-4 py-5">{renderPage()}</main>
    </div>
  )
}
