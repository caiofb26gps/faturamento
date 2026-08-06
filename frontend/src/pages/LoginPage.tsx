import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Alert, Button, Paper, PasswordInput, Stack, TextInput, Title } from '@mantine/core'
import { useAuth } from '../auth/AuthContext'

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setErro(null)
    setEnviando(true)
    try {
      await login(email, senha)
      navigate('/clientes')
    } catch {
      setErro('E-mail ou senha inválidos.')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <Stack align="center" justify="center" h="100vh" bg="gray.0">
      <Paper withBorder shadow="sm" p="xl" radius="md" w={380}>
        <Title order={3} mb="md">
          Mapa de Faturamento
        </Title>
        <form onSubmit={handleSubmit}>
          <Stack>
            {erro && <Alert color="red">{erro}</Alert>}
            <TextInput
              label="E-mail"
              value={email}
              onChange={(e) => setEmail(e.currentTarget.value)}
              required
              autoFocus
            />
            <PasswordInput
              label="Senha"
              value={senha}
              onChange={(e) => setSenha(e.currentTarget.value)}
              required
            />
            <Button type="submit" loading={enviando} fullWidth mt="sm">
              Entrar
            </Button>
          </Stack>
        </form>
      </Paper>
    </Stack>
  )
}
