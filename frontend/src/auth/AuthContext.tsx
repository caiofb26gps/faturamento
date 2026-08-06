import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { api } from '../api/client'
import type { Usuario } from '../api/types'

interface AuthContextValue {
  usuario: Usuario | null
  carregando: boolean
  login: (email: string, senha: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [usuario, setUsuario] = useState<Usuario | null>(null)
  const [carregando, setCarregando] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) {
      setCarregando(false)
      return
    }
    api
      .get<Usuario>('/auth/me')
      .then((r) => setUsuario(r.data))
      .catch(() => localStorage.removeItem('token'))
      .finally(() => setCarregando(false))
  }, [])

  async function login(email: string, senha: string) {
    const form = new URLSearchParams()
    form.set('username', email)
    form.set('password', senha)
    const { data } = await api.post('/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    localStorage.setItem('token', data.access_token)
    const { data: me } = await api.get<Usuario>('/auth/me')
    setUsuario(me)
  }

  function logout() {
    localStorage.removeItem('token')
    setUsuario(null)
  }

  return <AuthContext.Provider value={{ usuario, carregando, login, logout }}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth precisa estar dentro de <AuthProvider>')
  return ctx
}
