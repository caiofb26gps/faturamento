import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { Center, Loader } from '@mantine/core'
import { useAuth } from './AuthContext'

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { usuario, carregando } = useAuth()

  if (carregando) {
    return (
      <Center h="100vh">
        <Loader />
      </Center>
    )
  }

  if (!usuario) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}
