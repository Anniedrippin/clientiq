import React from 'react'
import { AuthProvider, useAuth } from './context/AuthContext'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'

function Shell() {
  const { user, initializing } = useAuth()
  if (initializing) return null
  return user ? <Dashboard /> : <Login />
}

export default function App() {
  return (
    <AuthProvider>
      <Shell />
    </AuthProvider>
  )
}
