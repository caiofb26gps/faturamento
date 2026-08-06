import enum


class PapelUsuario(str, enum.Enum):
    ADMIN = "ADMIN"
    ANALISTA = "ANALISTA"


class StatusCliente(str, enum.Enum):
    ATIVO = "ATIVO"
    PENDENTE = "PENDENTE"
    INATIVO = "INATIVO"


class StatusFolha(str, enum.Enum):
    ABERTA = "ABERTA"
    FECHADA = "FECHADA"


class TipoIdentificadorCliente(str, enum.Enum):
    COD_GRUPO = "COD_GRUPO"
    CNPJ = "CNPJ"
    RAZAO_SOCIAL = "RAZAO_SOCIAL"


class TipoImportacao(str, enum.Enum):
    CLOSED_INICIAL = "CLOSED_INICIAL"
    AJUSTE = "AJUSTE"


class StatusImportacao(str, enum.Enum):
    PROCESSANDO = "PROCESSANDO"
    CONCLUIDA = "CONCLUIDA"
    ERRO = "ERRO"


class StatusMapaGerado(str, enum.Enum):
    RASCUNHO = "RASCUNHO"
    PRONTO = "PRONTO"
    REVISADO = "REVISADO"
    ENVIADO = "ENVIADO"


class StatusEnvio(str, enum.Enum):
    PENDENTE = "PENDENTE"
    ENVIADO = "ENVIADO"


class AcaoAuditoria(str, enum.Enum):
    CRIACAO = "CRIACAO"
    EDICAO = "EDICAO"
    EXCLUSAO = "EXCLUSAO"
