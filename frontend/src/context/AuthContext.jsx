import React, { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { api, setAuthToken } from '../api/client'
import { logEvent } from '../api/logger'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(null)
  const [initializing, setInitializing] = useState(true)

  useEffect(() => {
    const saved = localStorage.getItem('clientiq_session')
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        setToken(parsed.access_token)
        setAuthToken(parsed.access_token)
        setUser({ username: parsed.username, role: parsed.role })
        logEvent('session_restored', 'info', { user: parsed.username })
      } catch (e) {
        logEvent('session_restore_failed', 'warning', { error: String(e) })
      }
    }
    setInitializing(false)
  }, [])

  const login = useCallback(async (username, password) => {
    const data = await api.login(username, password)
    setToken(data.access_token)
    setAuthToken(data.access_token)
    setUser({ username: data.username, role: data.role })
    localStorage.setItem('clientiq_session', JSON.stringify(data))
    return data
  }, [])

  const logout = useCallback(() => {
    logEvent('logout', 'info', { user: user?.username })
    setToken(null)
    setAuthToken(null)
    setUser(null)
    localStorage.removeItem('clientiq_session')
  }, [user])

  return (
    <AuthContext.Provider value={{ user, token, login, logout, initializing }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
