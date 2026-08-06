import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  Badge,
  Button,
  Group,
  Modal,
  Paper,
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
import type { Cliente, RegraSegmentacao, RegraSegmentacaoInput } from '../api/types'
import { useAuth } from '../auth/AuthContext'

const REGRA_VAZIA: RegraSegmentacaoInput = {
  valor_segmentacao: '',
  nome_exibicao: '',
  email_responsavel: '',
  dia_envio: null,
  envio_automatico: false,
  analista_id: null,
  aplica_email: true,
  aplica_mapa: true,
}

export function ClienteDetailPage() {
  const { clienteId } = useParams()
  const { usuario } = useAuth()
  const [cliente, setCliente] = useState<Cliente | null>(null)
  const [regras, setRegras] = useState<RegraSegmentacao[]>([])
  const [modalAberto, setModalAberto] = useState(false)

  const form = useForm<RegraSegmentacaoInput>({ initialValues: REGRA_VAZIA })

  async function carregar() {
    const [{ data: c }, { data: r }] = await Promise.all([
      api.get<Cliente>(`/clientes/${clienteId}`),
      api.get<RegraSegmentacao[]>(`/clientes/${clienteId}/regras`),
    ])
    setCliente(c)
    setRegras(r)
  }

  useEffect(() => {
    carregar()
  }, [clienteId])

  async function salvarRegra(values: RegraSegmentacaoInput) {
    try {
      await api.post(`/clientes/${clienteId}/regras`, values)
      notifications.show({ message: 'Regra criada.', color: 'green' })
      setModalAberto(false)
      form.reset()
      carregar()
    } catch (err: any) {
      notifications.show({ message: err?.response?.data?.detail ?? 'Erro ao criar regra', color: 'red' })
    }
  }

  if (!cliente) return null

  return (
    <Stack>
      <Group justify="space-between">
        <div>
          <Text size="sm" c="dimmed">
            <Link to="/clientes">← Clientes</Link>
          </Text>
          <Title order={2}>
            {cliente.nome}{' '}
            <Badge ml="xs" color={cliente.status === 'ATIVO' ? 'green' : 'yellow'}>
              {cliente.status}
            </Badge>
          </Title>
        </div>
      </Group>

      <Paper withBorder p="md">
        <Group gap="xl">
          <Text size="sm">
            <b>Negócio:</b> {cliente.negocio}
          </Text>
          <Text size="sm">
            <b>Segmentação e-mail:</b> {cliente.segmentacao_email}
          </Text>
          <Text size="sm">
            <b>Segmentação mapa:</b> {cliente.segmentacao_mapa}
          </Text>
          <Text size="sm">
            <b>Folha:</b> {cliente.folha}
          </Text>
          <Text size="sm">
            <b>Credenciais de portal:</b> {cliente.portal_credenciais_configuradas ? 'configuradas' : 'não configuradas'}
          </Text>
        </Group>
        {cliente.observacao && (
          <Text size="sm" mt="sm" c="dimmed">
            Observação: {cliente.observacao}
          </Text>
        )}
      </Paper>

      <Group justify="space-between">
        <Title order={4}>Regras de segmentação</Title>
        {usuario?.papel === 'ADMIN' && <Button size="xs" onClick={() => setModalAberto(true)}>Nova regra</Button>}
      </Group>

      <Table striped withTableBorder>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Valor</Table.Th>
            <Table.Th>Exibição</Table.Th>
            <Table.Th>E-mail responsável</Table.Th>
            <Table.Th>Dia envio</Table.Th>
            <Table.Th>Automático</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {regras.map((r) => (
            <Table.Tr key={r.id}>
              <Table.Td>{r.valor_segmentacao}</Table.Td>
              <Table.Td>{r.nome_exibicao}</Table.Td>
              <Table.Td>{r.email_responsavel}</Table.Td>
              <Table.Td>{r.dia_envio ?? '—'}</Table.Td>
              <Table.Td>{r.envio_automatico ? 'Sim' : 'Não'}</Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
      {regras.length === 0 && (
        <Text c="dimmed" size="sm">
          Este cliente usa segmentação GERAL — sem regras específicas.
        </Text>
      )}

      <Modal opened={modalAberto} onClose={() => setModalAberto(false)} title="Nova regra de segmentação">
        <form onSubmit={form.onSubmit(salvarRegra)}>
          <Stack>
            <TextInput
              label="Valor de segmentação"
              description="Ex: nome do colaborador, CNPJ, UF... conforme o tipo do cliente"
              required
              {...form.getInputProps('valor_segmentacao')}
            />
            <TextInput label="Nome de exibição no mapa" required {...form.getInputProps('nome_exibicao')} />
            <TextInput label="E-mail responsável" required {...form.getInputProps('email_responsavel')} />
            <TextInput
              label="Dia de envio"
              type="number"
              {...form.getInputProps('dia_envio')}
            />
            <Switch label="Envio automático" {...form.getInputProps('envio_automatico', { type: 'checkbox' })} />
            <Button type="submit">Salvar</Button>
          </Stack>
        </form>
      </Modal>
    </Stack>
  )
}
