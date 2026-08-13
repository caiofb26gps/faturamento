import { useEffect, useRef, useState } from 'react'
import {
  Alert,
  Badge,
  Button,
  FileInput,
  Group,
  Paper,
  Select,
  Stack,
  Table,
  Text,
  TextInput,
  Title,
} from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { api } from '../api/client'
import type { Cliente, Importacao, RegraSegmentacao, TipoImportacao } from '../api/types'

const COR_STATUS: Record<Importacao['status'], string> = {
  PROCESSANDO: 'blue',
  CONCLUIDA: 'green',
  ERRO: 'red',
}

function competenciaValida(valor: string) {
  if (!/^\d{6}$/.test(valor)) return false
  const mes = Number(valor.slice(4))
  return mes >= 1 && mes <= 12
}

export function ImportacoesPage() {
  const [importacoes, setImportacoes] = useState<Importacao[]>([])
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [regras, setRegras] = useState<RegraSegmentacao[]>([])

  const [arquivo, setArquivo] = useState<File | null>(null)
  const [competencia, setCompetencia] = useState('')
  const [tipo, setTipo] = useState<TipoImportacao>('CLOSED_INICIAL')
  const [clienteId, setClienteId] = useState<string | null>(null)
  const [regraId, setRegraId] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  // Guarda o id do intervalo pra poder parar o polling ao desmontar a tela.
  const intervalo = useRef<number | null>(null)

  async function carregarImportacoes() {
    const { data } = await api.get<Importacao[]>('/importacoes')
    setImportacoes(data)
    return data
  }

  useEffect(() => {
    carregarImportacoes()
    api.get<Cliente[]>('/clientes').then(({ data }) => setClientes(data))
    return () => {
      if (intervalo.current) window.clearInterval(intervalo.current)
    }
  }, [])

  // O processamento roda em background no backend (166k linhas), então a tela
  // consulta periodicamente enquanto houver algo em PROCESSANDO.
  useEffect(() => {
    const processando = importacoes.some((i) => i.status === 'PROCESSANDO')
    if (processando && !intervalo.current) {
      intervalo.current = window.setInterval(async () => {
        const atuais = await carregarImportacoes()
        if (!atuais.some((i) => i.status === 'PROCESSANDO') && intervalo.current) {
          window.clearInterval(intervalo.current)
          intervalo.current = null
        }
      }, 3000)
    }
  }, [importacoes])

  useEffect(() => {
    if (!clienteId) {
      setRegras([])
      setRegraId(null)
      return
    }
    api.get<RegraSegmentacao[]>(`/clientes/${clienteId}/regras`).then(({ data }) => setRegras(data))
  }, [clienteId])

  async function enviar() {
    if (!arquivo) {
      notifications.show({ message: 'Escolha o arquivo da DS (.xlsx)', color: 'red' })
      return
    }
    if (!competenciaValida(competencia)) {
      notifications.show({ message: 'Competência inválida — use AAAAMM, ex: 202607', color: 'red' })
      return
    }
    if (tipo === 'AJUSTE' && !clienteId) {
      notifications.show({ message: 'Ajuste pontual precisa de um cliente', color: 'red' })
      return
    }

    const form = new FormData()
    form.append('arquivo', arquivo)
    form.append('competencia', competencia)
    form.append('tipo', tipo)
    if (tipo === 'AJUSTE' && clienteId) form.append('cliente_id', clienteId)
    if (tipo === 'AJUSTE' && regraId) form.append('regra_segmentacao_id', regraId)

    setEnviando(true)
    try {
      await api.post('/importacoes', form)
      notifications.show({ message: 'Arquivo enviado — processando em segundo plano.', color: 'green' })
      setArquivo(null)
      carregarImportacoes()
    } catch (err: any) {
      notifications.show({ message: err?.response?.data?.detail ?? 'Erro ao enviar arquivo', color: 'red' })
    } finally {
      setEnviando(false)
    }
  }

  function nomeCliente(id: number | null) {
    if (!id) return '—'
    return clientes.find((c) => c.id === id)?.nome ?? `#${id}`
  }

  return (
    <Stack>
      <Title order={2}>Importação da DS</Title>

      <Paper withBorder p="md">
        <Stack>
          <Group align="flex-end" wrap="wrap">
            <FileInput
              label="Arquivo da DS"
              description="Planilha .xlsx com a aba de lançamentos"
              placeholder="Selecionar arquivo"
              accept=".xlsx,.xlsm"
              value={arquivo}
              onChange={setArquivo}
              w={280}
            />
            <TextInput
              label="Competência"
              description="AAAAMM"
              placeholder="202607"
              value={competencia}
              onChange={(e) => setCompetencia(e.currentTarget.value)}
              w={140}
            />
            <Select
              label="Tipo"
              data={[
                { value: 'CLOSED_INICIAL', label: 'Closed inicial (todos os clientes)' },
                { value: 'AJUSTE', label: 'Ajuste pontual (um cliente)' },
              ]}
              value={tipo}
              onChange={(v) => setTipo((v as TipoImportacao) ?? 'CLOSED_INICIAL')}
              w={280}
            />
          </Group>

          {tipo === 'AJUSTE' && (
            <Group align="flex-end" wrap="wrap">
              <Select
                label="Cliente"
                description="Obrigatório no ajuste"
                data={clientes.map((c) => ({ value: String(c.id), label: `${c.nome} (${c.negocio})` }))}
                value={clienteId}
                onChange={setClienteId}
                searchable
                clearable
                w={320}
              />
              <Select
                label="Regra (opcional)"
                description="Escope o ajuste a um destinatário específico"
                data={regras.map((r) => ({ value: String(r.id), label: `${r.nome_exibicao} — ${r.email_responsavel}` }))}
                value={regraId}
                onChange={setRegraId}
                searchable
                clearable
                disabled={!clienteId}
                w={420}
              />
            </Group>
          )}

          <Group>
            <Button loading={enviando} onClick={enviar}>
              Enviar arquivo
            </Button>
            <Text size="xs" c="dimmed">
              O processamento roda em segundo plano — a lista abaixo atualiza sozinha.
            </Text>
          </Group>
        </Stack>
      </Paper>

      <Title order={4}>Importações recentes</Title>

      <Table striped withTableBorder>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Competência</Table.Th>
            <Table.Th>Tipo</Table.Th>
            <Table.Th>Cliente</Table.Th>
            <Table.Th>Status</Table.Th>
            <Table.Th>Linhas resolvidas</Table.Th>
            <Table.Th>Enviado em</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {importacoes.map((i) => (
            <Table.Tr key={i.id}>
              <Table.Td>{i.competencia}</Table.Td>
              <Table.Td>{i.tipo === 'CLOSED_INICIAL' ? 'Closed inicial' : 'Ajuste'}</Table.Td>
              <Table.Td>{nomeCliente(i.cliente_id)}</Table.Td>
              <Table.Td>
                <Badge color={COR_STATUS[i.status]}>{i.status}</Badge>
              </Table.Td>
              <Table.Td>
                {i.resumo?.total_linhas
                  ? `${i.resumo.linhas_resolvidas ?? 0} de ${i.resumo.total_linhas}`
                  : i.status === 'PROCESSANDO'
                    ? '...'
                    : '—'}
              </Table.Td>
              <Table.Td>{new Date(i.criado_em).toLocaleString('pt-BR')}</Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
      {importacoes.length === 0 && (
        <Text c="dimmed" size="sm">
          Nenhuma importação ainda.
        </Text>
      )}

      {importacoes
        .filter((i) => i.status === 'ERRO' && i.mensagem_erro)
        .slice(0, 3)
        .map((i) => (
          <Alert key={i.id} color="red" title={`Erro na importação ${i.competencia}`}>
            {i.mensagem_erro}
          </Alert>
        ))}

      {importacoes
        .filter((i) => i.status === 'CONCLUIDA' && (i.resumo?.linhas_nao_resolvidas ?? 0) > 0)
        .slice(0, 1)
        .map((i) => (
          <Alert key={i.id} color="yellow" title={`${i.resumo?.linhas_nao_resolvidas} linha(s) sem cliente identificado`}>
            <Text size="sm" mb="xs">
              Essas linhas não entraram em nenhum mapa porque o sistema não soube a qual cliente cadastrado elas
              pertencem. Os maiores casos:
            </Text>
            <Stack gap={2}>
              {(i.resumo?.principais_nao_resolvidos ?? []).slice(0, 8).map((p, idx) => (
                <Text key={idx} size="xs">
                  {p.linhas} linha(s) — {p.grupo_cliente} (negócio {p.negocio_ds}, grupo {p.cod_grupo})
                </Text>
              ))}
            </Stack>
          </Alert>
        ))}
    </Stack>
  )
}
