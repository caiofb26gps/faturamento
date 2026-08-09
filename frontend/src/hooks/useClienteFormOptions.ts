import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { AtributoSegmentacao, Cliente, DeParaModelo, Usuario } from '../api/types'

// Atributos que o motor de geração de mapa (backend) já sabe resolver — ver
// ATRIBUTO_PARA_CAMPO_LANCAMENTO em geracao_mapa.py. SRA/CTT vão ampliar essa
// lista quando entrarem; até lá, oferecer outros códigos aqui só levaria a um
// erro "segmentação não suportada" na hora de gerar o mapa.
const ATRIBUTOS_SUPORTADOS = new Set(['COLABORADOR', 'CNPJ', 'CC', 'CARGO'])

export interface ClienteFormOptions {
  negocios: string[]
  atributosSegmentacao: { value: string; label: string }[]
  usuarios: { value: string; label: string }[]
  deParaModelos: { value: string; label: string }[]
}

export function useClienteFormOptions(): ClienteFormOptions {
  const [negocios, setNegocios] = useState<string[]>([])
  const [atributosSegmentacao, setAtributosSegmentacao] = useState<{ value: string; label: string }[]>([])
  const [usuarios, setUsuarios] = useState<{ value: string; label: string }[]>([])
  const [deParaModelos, setDeParaModelos] = useState<{ value: string; label: string }[]>([])

  useEffect(() => {
    api.get<Cliente[]>('/clientes').then(({ data }) => {
      setNegocios([...new Set(data.map((c) => c.negocio))].sort())
    })
    api.get<AtributoSegmentacao[]>('/atributos-segmentacao').then(({ data }) => {
      setAtributosSegmentacao(
        data
          .filter((a) => ATRIBUTOS_SUPORTADOS.has(a.codigo))
          .map((a) => ({ value: a.codigo, label: a.descricao ? `${a.codigo} — ${a.descricao}` : a.codigo })),
      )
    })
    api
      .get<Usuario[]>('/usuarios')
      .then(({ data }) => setUsuarios(data.map((u) => ({ value: String(u.id), label: `${u.nome} (${u.email})` }))))
      .catch(() => setUsuarios([])) // analista comum não tem permissão de listar usuários
    api.get<DeParaModelo[]>('/de-para/modelos').then(({ data }) => {
      setDeParaModelos(data.map((m) => ({ value: String(m.id), label: m.nome })))
    })
  }, [])

  return { negocios, atributosSegmentacao, usuarios, deParaModelos }
}
