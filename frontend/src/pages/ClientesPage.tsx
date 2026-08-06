import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Badge,
  Button,
  Drawer,
  Group,
  Select,
  Stack,
  Switch,
  Table,
  Text,
  TextInput,
  Title,
} from '@mantine/core'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import { api } from '../api/client'
import type { Cliente, ClienteInput } from '../api/types'
import { useAuth } from '../auth/AuthContext'

const CLIENTE_VAZIO: ClienteInput = {
  negocio: '',
  nome: '',
  status: 'PENDENTE',
  segmentacao_email: 'GERAL',
  segmentacao_mapa: 'GERAL',
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

  const form = useForm<ClienteInput>({ initialValues: CLIENTE_VAZIO })

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

      <Table striped highlightOnHover withTableBorder>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Negócio</Table.Th>
            <Table.Th>Cliente</Table.Th>
            <Table.Th>Status</Table.Th>
            <Table.Th>Segmentação (e-mail / mapa)</Table.Th>
            <Table.Th>Folha</Table.Th>
            <Table.Th />
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {clientes.map((c) => (
            <Table.Tr key={c.id}>
              <Table.Td>{c.negocio}</Table.Td>
              <Table.Td>{c.nome}</Table.Td>
              <Table.Td>
                <Badge color={c.status === 'ATIVO' ? 'green' : c.status === 'PENDENTE' ? 'yellow' : 'gray'}>
                  {c.status}
                </Badge>
              </Table.Td>
              <Table.Td>
                {c.segmentacao_email} / {c.segmentacao_mapa}
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

      {!carregando && clientes.length === 0 && <Text c="dimmed">Nenhum cliente encontrado.</Text>}

      <Drawer opened={drawerAberto} onClose={() => setDrawerAberto(false)} title="Novo cliente" position="right" size="md">
        <form onSubmit={form.onSubmit(salvar)}>
          <Stack>
            <TextInput label="Negócio" required {...form.getInputProps('negocio')} />
            <TextInput label="Nome do cliente" required {...form.getInputProps('nome')} />
            <Select
              label="Status"
              data={['ATIVO', 'PENDENTE', 'INATIVO']}
              {...form.getInputProps('status')}
            />
            <TextInput label="Segmentação de e-mail" {...form.getInputProps('segmentacao_email')} />
            <TextInput label="Segmentação do mapa" {...form.getInputProps('segmentacao_mapa')} />
            <Select label="Folha" data={['ABERTA', 'FECHADA']} {...form.getInputProps('folha')} />
            <Switch label="Aguardo de PO" {...form.getInputProps('aguardo_po', { type: 'checkbox' })} />
            <TextInput label="Site do portal do cliente" {...form.getInputProps('portal_site')} />
            <TextInput label="Login do portal" {...form.getInputProps('portal_login')} />
            <TextInput label="Senha do portal" type="password" {...form.getInputProps('portal_senha')} />
            <TextInput label="Observação" {...form.getInputProps('observacao')} />
            <Button type="submit">Salvar</Button>
          </Stack>
        </form>
      </Drawer>
    </Stack>
  )
}
