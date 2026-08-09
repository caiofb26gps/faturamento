import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Badge, Button, Drawer, Group, Select, Stack, Table, Text, TextInput, Title } from '@mantine/core'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import { api } from '../api/client'
import { ClienteCamposForm } from '../components/ClienteCamposForm'
import { useClienteFormOptions } from '../hooks/useClienteFormOptions'
import type { Cliente, ClienteInput } from '../api/types'
import { useAuth } from '../auth/AuthContext'

const CLIENTE_VAZIO: ClienteInput = {
  negocio: '',
  nome: '',
  status: 'PENDENTE',
  de_para_modelo_id: null,
  modelo_mapa_codigo: 'GERAL',
  analista_responsavel_id: null,
  folha: 'FECHADA',
  aguardo_po: false,
  portal_site: null,
  observacao: null,
  portal_login: '',
  portal_senha: '',
}

export function ClientesPage() {
  const { usuario } = useAuth()
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [carregando, setCarregando] = useState(true)
  const [drawerAberto, setDrawerAberto] = useState(false)
  const [busca, setBusca] = useState('')
  const [filtroNegocio, setFiltroNegocio] = useState<string | null>(null)
  const [filtroStatus, setFiltroStatus] = useState<string | null>(null)

  const form = useForm<ClienteInput>({ initialValues: CLIENTE_VAZIO })
  const opcoes = useClienteFormOptions()

  async function carregar() {
    setCarregando(true)
    try {
      const { data } = await api.get<Cliente[]>('/clientes')
      setClientes(data)
    } finally {
      setCarregando(false)
    }
  }

  useEffect(() => {
    carregar()
  }, [])

  const negocios = [...new Set(clientes.map((c) => c.negocio))].sort()

  const clientesFiltrados = clientes.filter((c) => {
    if (busca && !c.nome.toLowerCase().includes(busca.toLowerCase())) return false
    if (filtroNegocio && c.negocio !== filtroNegocio) return false
    if (filtroStatus && c.status !== filtroStatus) return false
    return true
  })

  async function salvar(values: ClienteInput) {
    try {
      await api.post('/clientes', values)
      notifications.show({ message: `Cliente "${values.nome}" criado.`, color: 'green' })
      setDrawerAberto(false)
      form.reset()
      carregar()
    } catch (err: any) {
      notifications.show({
        message: err?.response?.data?.detail ?? 'Erro ao criar cliente',
        color: 'red',
      })
    }
  }

  return (
    <Stack>
      <Group justify="space-between">
        <Title order={2}>Clientes</Title>
        {usuario?.papel === 'ADMIN' && <Button onClick={() => setDrawerAberto(true)}>Novo cliente</Button>}
      </Group>

      <Group>
        <TextInput
          placeholder="Buscar por nome"
          value={busca}
          onChange={(e) => setBusca(e.currentTarget.value)}
          w={220}
        />
        <Select
          placeholder="Negócio"
          data={negocios}
          value={filtroNegocio}
          onChange={setFiltroNegocio}
          clearable
          w={160}
        />
        <Select
          placeholder="Status"
          data={['ATIVO', 'PENDENTE', 'INATIVO']}
          value={filtroStatus}
          onChange={setFiltroStatus}
          clearable
          w={160}
        />
        <Text size="sm" c="dimmed">
          {clientesFiltrados.length} de {clientes.length}
        </Text>
      </Group>

      <Table striped highlightOnHover withTableBorder>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Negócio</Table.Th>
            <Table.Th>Cliente</Table.Th>
            <Table.Th>Status</Table.Th>
            <Table.Th>Segmentação</Table.Th>
            <Table.Th>Folha</Table.Th>
            <Table.Th />
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {clientesFiltrados.map((c) => (
            <Table.Tr key={c.id}>
              <Table.Td>{c.negocio}</Table.Td>
              <Table.Td>{c.nome}</Table.Td>
              <Table.Td>
                <Badge color={c.status === 'ATIVO' ? 'green' : c.status === 'PENDENTE' ? 'yellow' : 'gray'}>
                  {c.status}
                </Badge>
              </Table.Td>
              <Table.Td>
                {c.total_regras === 0 ? (
                  <Badge variant="light">GERAL</Badge>
                ) : (
                  `${c.total_regras} regra(s)`
                )}
              </Table.Td>
              <Table.Td>{c.folha}</Table.Td>
              <Table.Td>
                <Button component={Link} to={`/clientes/${c.id}`} size="xs" variant="light">
                  Abrir
                </Button>
              </Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>

      {!carregando && clientesFiltrados.length === 0 && <Text c="dimmed">Nenhum cliente encontrado.</Text>}

      <Drawer opened={drawerAberto} onClose={() => setDrawerAberto(false)} title="Novo cliente" position="right" size="md">
        <form onSubmit={form.onSubmit(salvar)}>
          <Stack>
            <ClienteCamposForm form={form} opcoes={opcoes} />
            <Button type="submit">Salvar</Button>
          </Stack>
        </form>
      </Drawer>
    </Stack>
  )
}
