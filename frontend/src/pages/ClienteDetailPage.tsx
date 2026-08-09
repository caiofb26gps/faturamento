import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  Alert,
  Badge,
  Button,
  Drawer,
  Group,
  Modal,
  Paper,
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
import { ClienteCamposForm } from '../components/ClienteCamposForm'
import { useClienteFormOptions } from '../hooks/useClienteFormOptions'
import type {
  Cliente,
  ClienteInput,
  ForaDasRegras,
  GeracaoMapaResultado,
  MapaGerado,
  RegraSegmentacao,
  RegraSegmentacaoInput,
} from '../api/types'
import { useAuth } from '../auth/AuthContext'

function corStatusMapa(status: MapaGerado['status']) {
  return { RASCUNHO: 'yellow', PRONTO: 'blue', REVISADO: 'teal', ENVIADO: 'green' }[status]
}

const CLIENTE_INPUT_VAZIO: ClienteInput = {
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
  portal_login: null,
  portal_senha: null,
}

const REGRA_VAZIA: RegraSegmentacaoInput = {
  ordem: 0,
  atributo_segmentacao: '',
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
  const [mapas, setMapas] = useState<MapaGerado[]>([])
  const [foraDasRegras, setForaDasRegras] = useState<ForaDasRegras | null>(null)
  const [modalAberto, setModalAberto] = useState(false)
  const [drawerEdicaoAberto, setDrawerEdicaoAberto] = useState(false)
  const [competencia, setCompetencia] = useState('')
  const [gerando, setGerando] = useState(false)

  const form = useForm<RegraSegmentacaoInput>({ initialValues: REGRA_VAZIA })
  const formEdicao = useForm<ClienteInput>({ initialValues: CLIENTE_INPUT_VAZIO })
  const opcoes = useClienteFormOptions()

  async function carregar() {
    const [{ data: c }, { data: r }, { data: m }] = await Promise.all([
      api.get<Cliente>(`/clientes/${clienteId}`),
      api.get<RegraSegmentacao[]>(`/clientes/${clienteId}/regras`),
      api.get<MapaGerado[]>(`/clientes/${clienteId}/mapas`),
    ])
    setCliente(c)
    setRegras(r)
    setMapas(m)
  }

  async function gerarMapas() {
    if (!competencia) {
      notifications.show({ message: 'Informe a competência (formato AAAAMM, ex: 202607)', color: 'red' })
      return
    }
    setGerando(true)
    try {
      const { data } = await api.post<GeracaoMapaResultado>(`/clientes/${clienteId}/mapas/gerar`, null, {
        params: { competencia },
      })
      notifications.show({ message: `${data.mapas.length} mapa(s) gerado(s).`, color: 'green' })
      setForaDasRegras(data.fora_das_regras)
      carregar()
    } catch (err: any) {
      notifications.show({ message: err?.response?.data?.detail ?? 'Erro ao gerar mapa', color: 'red' })
    } finally {
      setGerando(false)
    }
  }

  async function baixarMapa(mapa: MapaGerado) {
    const { data } = await api.get(`/mapas/${mapa.id}/arquivo`, { responseType: 'blob' })
    const url = URL.createObjectURL(data)
    const link = document.createElement('a')
    link.href = url
    link.download = `mapa_${mapa.competencia}_cliente${mapa.cliente_id}_${mapa.id}.xlsx`
    link.click()
    URL.revokeObjectURL(url)
  }

  function abrirEdicao() {
    if (!cliente) return
    formEdicao.setValues({
      negocio: cliente.negocio,
      nome: cliente.nome,
      status: cliente.status,
      de_para_modelo_id: cliente.de_para_modelo_id,
      modelo_mapa_codigo: cliente.modelo_mapa_codigo,
      analista_responsavel_id: cliente.analista_responsavel_id,
      folha: cliente.folha,
      aguardo_po: cliente.aguardo_po,
      portal_site: cliente.portal_site,
      observacao: cliente.observacao,
      portal_login: null,
      portal_senha: null,
    })
    setDrawerEdicaoAberto(true)
  }

  async function salvarEdicao(values: ClienteInput) {
    try {
      await api.put(`/clientes/${clienteId}`, values)
      notifications.show({ message: 'Cliente atualizado.', color: 'green' })
      setDrawerEdicaoAberto(false)
      carregar()
    } catch (err: any) {
      notifications.show({ message: err?.response?.data?.detail ?? 'Erro ao atualizar cliente', color: 'red' })
    }
  }

  useEffect(() => {
    carregar()
  }, [clienteId])

  function abrirNovaRegra() {
    form.setValues({ ...REGRA_VAZIA, ordem: regras.length })
    setModalAberto(true)
  }

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

  async function mover(regra: RegraSegmentacao, direcao: -1 | 1) {
    const posicaoAtual = regras.findIndex((r) => r.id === regra.id)
    const novaPosicao = posicaoAtual + direcao
    if (novaPosicao < 0 || novaPosicao >= regras.length) return

    const novaOrdem = [...regras]
    ;[novaOrdem[posicaoAtual], novaOrdem[novaPosicao]] = [novaOrdem[novaPosicao], novaOrdem[posicaoAtual]]
    setRegras(novaOrdem) // otimista

    try {
      await api.put(`/clientes/${clienteId}/regras/reordenar`, novaOrdem.map((r) => r.id))
      carregar()
    } catch (err: any) {
      notifications.show({ message: err?.response?.data?.detail ?? 'Erro ao reordenar', color: 'red' })
      carregar()
    }
  }

  function regraDoMapa(mapa: MapaGerado): RegraSegmentacao | undefined {
    return regras.find((r) => r.id === mapa.regra_segmentacao_id)
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
        {usuario?.papel === 'ADMIN' && <Button variant="light" onClick={abrirEdicao}>Editar</Button>}
      </Group>

      <Paper withBorder p="md">
        <Group gap="xl">
          <Text size="sm">
            <b>Negócio:</b> {cliente.negocio}
          </Text>
          <Text size="sm">
            <b>Folha:</b> {cliente.folha}
          </Text>
          <Text size="sm">
            <b>De/Para:</b>{' '}
            {opcoes.deParaModelos.find((m) => m.value === String(cliente.de_para_modelo_id))?.label ?? '—'}
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
        <div>
          <Title order={4}>Regras de segmentação</Title>
          <Text size="xs" c="dimmed">
            Testadas em ordem — a primeira que bater vence (&quot;grande SE&quot;). Sem nenhuma regra = mapa único (GERAL).
          </Text>
        </div>
        {usuario?.papel === 'ADMIN' && <Button size="xs" onClick={abrirNovaRegra}>Nova regra</Button>}
      </Group>

      <Table striped withTableBorder>
        <Table.Thead>
          <Table.Tr>
            <Table.Th />
            <Table.Th>Se atributo</Table.Th>
            <Table.Th>For igual a</Table.Th>
            <Table.Th>Exibição</Table.Th>
            <Table.Th>E-mail responsável</Table.Th>
            <Table.Th>Dia envio</Table.Th>
            <Table.Th>Automático</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {regras.map((r, i) => (
            <Table.Tr key={r.id}>
              <Table.Td>
                {usuario?.papel === 'ADMIN' && (
                  <Group gap={2}>
                    <Button size="compact-xs" variant="subtle" disabled={i === 0} onClick={() => mover(r, -1)}>
                      ↑
                    </Button>
                    <Button size="compact-xs" variant="subtle" disabled={i === regras.length - 1} onClick={() => mover(r, 1)}>
                      ↓
                    </Button>
                  </Group>
                )}
              </Table.Td>
              <Table.Td>
                <Badge variant="light">{r.atributo_segmentacao}</Badge>
              </Table.Td>
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
          Este cliente não tem regras — vai gerar um único mapa (GERAL).
        </Text>
      )}

      <Group justify="space-between" mt="md">
        <Title order={4}>Mapas de faturamento</Title>
        <Group>
          <TextInput
            placeholder="Competência (AAAAMM)"
            value={competencia}
            onChange={(e) => setCompetencia(e.currentTarget.value)}
            w={160}
          />
          <Button size="xs" loading={gerando} onClick={gerarMapas}>
            Gerar mapa
          </Button>
        </Group>
      </Group>

      {foraDasRegras && foraDasRegras.quantidade > 0 && (
        <Alert color="red" title={`${foraDasRegras.quantidade} colaborador(es) fora das regras`}>
          Não bateram em nenhuma regra desta competência — não entraram em nenhum mapa. Cadastre uma regra pra eles:{' '}
          {foraDasRegras.colaboradores
            .slice(0, 10)
            .map((c) => c.colaborador ?? c.matricula)
            .join(', ')}
          {foraDasRegras.quantidade > 10 ? ` e mais ${foraDasRegras.quantidade - 10}...` : ''}
        </Alert>
      )}

      <Table striped withTableBorder>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Competência</Table.Th>
            <Table.Th>Destinatário</Table.Th>
            <Table.Th>Status</Table.Th>
            <Table.Th>Total</Table.Th>
            <Table.Th>Alertas</Table.Th>
            <Table.Th />
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {mapas.map((m) => {
            const regra = regraDoMapa(m)
            return (
              <Table.Tr key={m.id}>
                <Table.Td>{m.competencia}</Table.Td>
                <Table.Td>{regra ? `${regra.nome_exibicao} (${regra.email_responsavel})` : 'GERAL'}</Table.Td>
                <Table.Td>
                  <Badge color={corStatusMapa(m.status)}>{m.status}</Badge>
                </Table.Td>
                <Table.Td>{m.valores_iniciais?.Total ?? '—'}</Table.Td>
                <Table.Td>
                  {m.alertas?.verbas_fora_de_para?.length ? (
                    <Badge color="orange">{m.alertas.verbas_fora_de_para.length} verba(s) fora do De/Para</Badge>
                  ) : null}
                </Table.Td>
                <Table.Td>
                  <Button size="xs" variant="light" onClick={() => baixarMapa(m)}>
                    Baixar .xlsx
                  </Button>
                </Table.Td>
              </Table.Tr>
            )
          })}
        </Table.Tbody>
      </Table>
      {mapas.length === 0 && (
        <Text c="dimmed" size="sm">
          Nenhum mapa gerado ainda para este cliente.
        </Text>
      )}

      <Modal opened={modalAberto} onClose={() => setModalAberto(false)} title="Nova regra de segmentação">
        <form onSubmit={form.onSubmit(salvarRegra)}>
          <Stack>
            <Select
              label="Se o atributo"
              description="Qual dado do colaborador essa regra testa"
              data={opcoes.atributosSegmentacao}
              required
              {...form.getInputProps('atributo_segmentacao')}
            />
            <TextInput
              label="For igual a"
              description="Ex: um CNPJ, um cargo, o nome do colaborador — conforme o atributo escolhido"
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
            <Text size="xs" c="dimmed">
              Vai entrar no fim da fila de prioridade (posição {form.values.ordem + 1}) — reordene depois com as flechinhas se precisar testar antes de outra regra.
            </Text>
            <Button type="submit">Salvar</Button>
          </Stack>
        </form>
      </Modal>

      <Drawer opened={drawerEdicaoAberto} onClose={() => setDrawerEdicaoAberto(false)} title="Editar cliente" position="right" size="md">
        <form onSubmit={formEdicao.onSubmit(salvarEdicao)}>
          <Stack>
            <ClienteCamposForm form={formEdicao} opcoes={opcoes} />
            <Button type="submit">Salvar</Button>
          </Stack>
        </form>
      </Drawer>
    </Stack>
  )
}
