import type { ReactNode } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { AppShell, Group, Text, Button, NavLink, Badge } from '@mantine/core'
import { useAuth } from '../auth/AuthContext'

export function AppLayout({ children }: { children: ReactNode }) {
  const { usuario, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <AppShell header={{ height: 60 }} navbar={{ width: 220, breakpoint: 'sm' }} padding="md">
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <Text fw={700}>Mapa de Faturamento</Text>
          <Group>
            <Text size="sm">{usuario?.nome}</Text>
            {usuario?.papel === 'ADMIN' && <Badge color="grape">admin</Badge>}
            <Button size="xs" variant="subtle" onClick={handleLogout}>
              Sair
            </Button>
          </Group>
        </Group>
      </AppShell.Header>

      <AppShell.Navbar p="md">
        <NavLink component={Link} to="/clientes" label="Clientes" />
        <NavLink component={Link} to="/de-para" label="De/Para geral" />
      </AppShell.Navbar>

      <AppShell.Main bg="gray.0">{children}</AppShell.Main>
    </AppShell>
  )
}
