import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Badge, Button, Group, Stack, Table, Title } from '@mantine/core'
import { api } from '../api/client'
import type { DeParaModelo } from '../api/types'

export function DeParaPage() {
  const [modelos, setModelos] = useState<DeParaModelo[]>([])

  useEffect(() => {
    api.get<DeParaModelo[]>('/de-para/modelos').then(({ data }) => setModelos(data))
  }, [])

  return (
    <Stack>
      <Group justify="space-between">
        <Title order={2}>De/Para de verbas</Title>
      </Group>

      <Table striped highlightOnHover withTableBorder>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Nome</Table.Th>
            <Table.Th>Usado por</Table.Th>
            <Table.Th>Itens</Table.Th>
            <Table.Th />
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {modelos.map((m) => (
            <Table.Tr key={m.id}>
              <Table.Td>
                {m.nome}
                {m.nome === 'GERAL' && (
                  <Badge ml="xs" size="sm" variant="light">
                    padrão
                  </Badge>
                )}
              </Table.Td>
              <Table.Td>
                {m.clientes_vinculados.length === 0
                  ? '—'
                  : m.clientes_vinculados.length <= 2
                    ? m.clientes_vinculados.join(', ')
                    : `${m.clientes_vinculados.length} clientes`}
              </Table.Td>
              <Table.Td>{m.total_itens}</Table.Td>
              <Table.Td>
                <Button component={Link} to={`/de-para/${m.id}`} size="xs" variant="light">
                  Abrir
                </Button>
              </Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
      {modelos.length === 0 && <div>Nenhum De/Para cadastrado ainda.</div>}
    </Stack>
  )
}
