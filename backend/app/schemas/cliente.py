from pydantic import BaseModel

from app.models.enums import StatusCliente, StatusFolha


class ClienteIdentificadorOut(BaseModel):
    id: int
    negocio: str
    tipo: str
    valor: str

    model_config = {"from_attributes": True}


class ClienteIdentificadorCreate(BaseModel):
    negocio: str
    tipo: str
    valor: str


class ClienteBase(BaseModel):
    negocio: str
    nome: str
    status: StatusCliente = StatusCliente.PENDENTE
    de_para_modelo_id: int | None = None
    modelo_mapa_codigo: str = "GERAL"
    analista_responsavel_id: int | None = None
    folha: StatusFolha = StatusFolha.FECHADA
    aguardo_po: bool = False
    portal_site: str | None = None
    observacao: str | None = None


class ClienteCreate(ClienteBase):
    # Credenciais chegam em texto puro apenas nesta requisição (idealmente via HTTPS)
    # e são criptografadas antes de persistir — nunca gravadas nem devolvidas em claro.
    portal_login: str | None = None
    portal_senha: str | None = None


class ClienteUpdate(ClienteCreate):
    pass


class ClienteOut(ClienteBase):
    id: int
    portal_credenciais_configuradas: bool = False
    total_regras: int = 0

    model_config = {"from_attributes": True}
