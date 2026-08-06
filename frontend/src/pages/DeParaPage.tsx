import { useEffect, useState } from 'react'
import { Select, Stack, Table, Title } from '@mantine/core'
import { api } from '../api/client'

interface DeParaModelo {
  id: number
  nome: string
  cliente_id: number | null
}

interface DeParaVerba {
  id: number
  verba_codigo: string
  descricao_original: string | null
  evento_exibicao: string
  grupo: string
  ordem_grupo: number
  ordem_item: number
}

export function DeParaPage() {
  const [modelos, setModelos] = useState<DeParaModelo[]>([])
  const [modeloId, setModeloId] = useState<string | null>(null)
  const [itens, setItens] = useState<DeParaVerba[]>([])

  useEffect(() => {
    api.get<DeParaModelo[]>('/de-para/modelos').then(({ data }) => {
      setModelos(data)
      const geral = data.find((m) => m.nome === 'GERAL' && m.cliente_id === null)
      if (geral) setModeloId(String(geral.id))
    })
  }, [])

  useEffect(() => {
    if (!modeloId) return
    api.get<DeParaVerba[]>(`/de-para/modelos/${modeloId}/itens`).then(({ data }) => setItens(data))
  }, [modeloId])

  return (
    <Stack>
      <Title order={2}>De/Para de verbas</Title>
      <Select
        label="Modelo"
        data={modelos.map((m) => ({ value: String(m.id), label: m.cliente_id ? `${m.nome} (cliente #${m.cliente_id})` : m.nome }))}
        value={modeloId}
        onChange={setModeloId}
        w={300}
      />
      <Table striped withTableBorder>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Verba</Table.Th>
            <Table.Th>Descrição original</Table.Th>
            <Table.Th>Evento (exibição)</Table.Th>
            <Table.Th>Grupo</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {itens.map((i) => (
            <Table.Tr key={i.id}>
              <Table.Td>{i.verba_codigo}</Table.Td>
              <Table.Td>{i.descricao_original}</Table.Td>
              <Table.Td>{i.evento_exibicao}</Table.Td>
              <Table.Td>{i.grupo}</Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
    </Stack>
  )
}
