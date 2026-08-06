export type PapelUsuario = 'ADMIN' | 'ANALISTA'
export type StatusCliente = 'ATIVO' | 'PENDENTE' | 'INATIVO'
export type StatusFolha = 'ABERTA' | 'FECHADA'

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
  segmentacao_email: string
  segmentacao_mapa: string
  de_para_modelo_id: number | null
  modelo_mapa_codigo: string
  analista_responsavel_id: number | null
  folha: StatusFolha
  aguardo_po: boolean
  portal_site: string | null
  observacao: string | null
  portal_credenciais_configuradas: boolean
}

export interface ClienteInput {
  negocio: string
  nome: string
  status: StatusCliente
  segmentacao_email: string
  segmentacao_mapa: string
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
  alertas: { fora_das_regras: boolean; verbas_fora_de_para: string[] } | null
}
