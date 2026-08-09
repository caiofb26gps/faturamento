import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Badge, Group, Stack, Table, Text, Title } from '@mantine/core'
import { api } from '../api/client'
import type { DeParaModelo, DeParaVerba } from '../api/types'

export function DeParaDetailPage() {
  const { modeloId } = useParams()
  const [modelo, setModelo] = useState<DeParaModelo | null>(null)
  const [itens, setItens] = useState<DeParaVerba[]>([])

  useEffect(() => {
    api.get<DeParaModelo>(`/de-para/modelos/${modeloId}`).then(({ data }) => setModelo(data))
    api.get<DeParaVerba[]>(`/de-para/modelos/${modeloId}/itens`).then(({ data }) => setItens(data))
  }, [modeloId])

  if (!modelo) return null

  return (
    <Stack>
      <div>
        <Text size="sm" c="dimmed">
          <Link to="/de-para">← De/Para de verbas</Link>
        </Text>
        <Group gap="xs">
          <Title order={2}>{modelo.nome}</Title>
          {modelo.nome === 'GERAL' && <Badge variant="light">padrão</Badge>}
        </Group>
        <Text size="sm" c="dimmed">
          {modelo.clientes_vinculados.length === 0
            ? 'Nenhum cliente usando este De/Para ainda.'
            : `Usado por: ${modelo.clientes_vinculados.join(', ')}`}
        </Text>
      </div>

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
      {itens.length === 0 && <Text c="dimmed">Nenhum item cadastrado neste De/Para.</Text>}
    </Stack>
  )
}
