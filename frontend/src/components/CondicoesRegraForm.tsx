import { ActionIcon, Button, Group, SegmentedControl, Select, Stack, Text, TextInput } from '@mantine/core'
import type { ComparadorCondicao, LogicaRegra, RegraCondicaoInput } from '../api/types'

const COMPARADORES: { value: ComparadorCondicao; label: string }[] = [
  { value: 'IGUAL', label: 'é igual a' },
  { value: 'CONTEM', label: 'contém' },
  { value: 'DIFERENTE', label: 'é diferente de' },
]

export function CondicoesRegraForm({
  logica,
  condicoes,
  atributos,
  onLogicaChange,
  onCondicoesChange,
}: {
  logica: LogicaRegra
  condicoes: RegraCondicaoInput[]
  atributos: { value: string; label: string }[]
  onLogicaChange: (l: LogicaRegra) => void
  onCondicoesChange: (c: RegraCondicaoInput[]) => void
}) {
  function atualizar(indice: number, mudanca: Partial<RegraCondicaoInput>) {
    onCondicoesChange(condicoes.map((c, i) => (i === indice ? { ...c, ...mudanca } : c)))
  }

  function adicionar() {
    onCondicoesChange([...condicoes, { atributo: '', comparador: 'IGUAL', valor: '' }])
  }

  function remover(indice: number) {
    onCondicoesChange(condicoes.filter((_, i) => i !== indice))
  }

  return (
    <Stack gap="xs">
      <Text size="sm" fw={500}>
        Condições
      </Text>

      {condicoes.length > 1 && (
        <Group gap="xs">
          <Text size="xs" c="dimmed">
            Combinar condições com:
          </Text>
          <SegmentedControl
            size="xs"
            value={logica}
            onChange={(v) => onLogicaChange(v as LogicaRegra)}
            data={[
              { value: 'E', label: 'E (todas)' },
              { value: 'OU', label: 'OU (qualquer uma)' },
            ]}
          />
        </Group>
      )}

      {condicoes.map((c, i) => (
        <Group key={i} gap="xs" align="flex-end" wrap="nowrap">
          <Text size="xs" c="dimmed" w={28} ta="right" pb={8}>
            {i === 0 ? 'SE' : logica}
          </Text>
          <Select
            placeholder="Atributo"
            data={atributos}
            value={c.atributo || null}
            onChange={(v) => atualizar(i, { atributo: v ?? '' })}
            searchable
            w={150}
          />
          <Select
            data={COMPARADORES}
            value={c.comparador}
            onChange={(v) => atualizar(i, { comparador: (v as ComparadorCondicao) ?? 'IGUAL' })}
            w={140}
            allowDeselect={false}
          />
          <TextInput
            placeholder="Valor"
            value={c.valor}
            onChange={(e) => atualizar(i, { valor: e.currentTarget.value })}
            style={{ flex: 1 }}
          />
          <ActionIcon
            variant="subtle"
            color="red"
            onClick={() => remover(i)}
            disabled={condicoes.length === 1}
            title={condicoes.length === 1 ? 'A regra precisa de ao menos uma condição' : 'Remover condição'}
            mb={2}
          >
            ✕
          </ActionIcon>
        </Group>
      ))}

      <Button size="compact-xs" variant="light" onClick={adicionar} w="fit-content">
        + Adicionar condição
      </Button>
    </Stack>
  )
}
