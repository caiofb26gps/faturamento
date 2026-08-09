export type PapelUsuario = 'ADMIN' | 'ANALISTA'
export type StatusCliente = 'ATIVO' | 'PENDENTE' | 'INATIVO'
export type StatusFolha = 'ABERTA' | 'FECHADA'

export interface DeParaModelo {
  id: number
  nome: string
  total_itens: number
  clientes_vinculados: string[]
}

export interface DeParaVerba {
  id: number
  de_para_modelo_id: number
  verba_codigo: string
  descricao_original: string | null
  evento_exibicao: string
  grupo: string
  ordem_grupo: number
  ordem_item: number
}

export interface Usuario {
  id: number
  nome: string
  email: string
  papel: PapelUsuario
  ativo: boolean
}

export interface Cliente {
  id: number
  negocio: string
  nome: string
  status: StatusCliente
  de_para_modelo_id: number | null
  modelo_mapa_codigo: string
  analista_responsavel_id: number | null
  folha: StatusFolha
  aguardo_po: boolean
  portal_site: string | null
  observacao: string | null
  portal_credenciais_configuradas: boolean
  total_regras: number
}

export interface ClienteInput {
  negocio: string
  nome: string
  status: StatusCliente
  de_para_modelo_id: number | null
  modelo_mapa_codigo: string
  analista_responsavel_id: number | null
  folha: StatusFolha
  aguardo_po: boolean
  portal_site: string | null
  observacao: string | null
  portal_login?: string | null
  portal_senha?: string | null
}

export interface RegraSegmentacao {
  id: number
  cliente_id: number
  ordem: number
  atributo_segmentacao: string
  valor_segmentacao: string
  nome_exibicao: string
  email_responsavel: string
  dia_envio: number | null
  envio_automatico: boolean
  analista_id: number | null
  aplica_email: boolean
  aplica_mapa: boolean
}

export interface RegraSegmentacaoInput {
  ordem: number
  atributo_segmentacao: string
  valor_segmentacao: string
  nome_exibicao: string
  email_responsavel: string
  dia_envio: number | null
  envio_automatico: boolean
  analista_id: number | null
  aplica_email: boolean
  aplica_mapa: boolean
}

export interface AtributoSegmentacao {
  id: number
  codigo: string
  descricao: string | null
}

export type StatusMapaGerado = 'RASCUNHO' | 'PRONTO' | 'REVISADO' | 'ENVIADO'

export interface MapaGerado {
  id: number
  cliente_id: number
  regra_segmentacao_id: number | null
  competencia: string
  status: StatusMapaGerado
  valores_iniciais: Record<string, string> | null
  valores_finais: Record<string, string> | null
  diferenca: Record<string, string> | null
  alertas: { verbas_fora_de_para: string[] } | null
}

export interface ForaDasRegras {
  quantidade: number
  colaboradores: { matricula: string | null; colaborador: string | null }[]
}

export interface GeracaoMapaResultado {
  mapas: MapaGerado[]
  fora_das_regras: ForaDasRegras
}
