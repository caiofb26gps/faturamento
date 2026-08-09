import { Select, Stack, Switch, Text, TextInput } from '@mantine/core'
import type { UseFormReturnType } from '@mantine/form'
import type { ClienteFormOptions } from '../hooks/useClienteFormOptions'
import type { ClienteInput } from '../api/types'

export function ClienteCamposForm({
  form,
  opcoes,
}: {
  form: UseFormReturnType<ClienteInput>
  opcoes: ClienteFormOptions
}) {
  return (
    <Stack>
      <Select
        label="Negócio"
        data={opcoes.negocios}
        searchable
        {...form.getInputProps('negocio')}
        onChange={(v) => form.setFieldValue('negocio', v ?? '')}
      />
      <TextInput label="Nome do cliente" required {...form.getInputProps('nome')} />
      <Select label="Status" data={['ATIVO', 'PENDENTE', 'INATIVO']} {...form.getInputProps('status')} />

      <Select
        label="De/Para de verbas"
        description="Qual conversão de verbas este cliente usa"
        data={opcoes.deParaModelos}
        value={form.values.de_para_modelo_id === null ? null : String(form.values.de_para_modelo_id)}
        onChange={(v) => form.setFieldValue('de_para_modelo_id', v ? Number(v) : null)}
        searchable
      />

      <Select label="Folha" data={['ABERTA', 'FECHADA']} {...form.getInputProps('folha')} />

      <Select
        label="Analista responsável"
        data={opcoes.usuarios}
        value={form.values.analista_responsavel_id === null ? null : String(form.values.analista_responsavel_id)}
        onChange={(v) => form.setFieldValue('analista_responsavel_id', v ? Number(v) : null)}
        searchable
        clearable
      />
      {opcoes.usuarios.length === 0 && (
        <Text size="xs" c="dimmed">
          Lista de analistas só é visível para administradores.
        </Text>
      )}

      <Switch label="Aguardo de PO" {...form.getInputProps('aguardo_po', { type: 'checkbox' })} />
      <TextInput label="Site do portal do cliente" {...form.getInputProps('portal_site')} />
      <TextInput label="Login do portal" {...form.getInputProps('portal_login')} />
      <TextInput label="Senha do portal" type="password" {...form.getInputProps('portal_senha')} />
      <TextInput label="Observação" {...form.getInputProps('observacao')} />
    </Stack>
  )
}
